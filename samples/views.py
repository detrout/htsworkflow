from __future__ import absolute_import, print_function, unicode_literals

# Create your views here.
import logging
import os
import json

from django.contrib.admin.sites import site as admin_site
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required

from htsworkflow.auth import require_api_key
from experiments.models import FlowCell, LANE_STATUS_MAP
from .changelist import HTSChangeList
from .models import Antibody, Library, Species
from .admin import LibraryOptions
from .results import get_flowcell_result_dict
from bcmagic.forms import BarcodeMagicForm
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines.samplekey import SampleKey
from htsworkflow.util.conversion import str_or_none, parse_flowcell_id
from htsworkflow.util import makebed
from htsworkflow.util import opener

LANE_LIST = [1, 2, 3, 4, 5, 6, 7, 8]
SAMPLES_CONTEXT_DEFAULTS = {
    'app_name': 'Flowcell/Library Tracker',
    'bcmagic': BarcodeMagicForm()
}

LOGGER = logging.getLogger(__name__)


def library_index(request, todo_only=False):
    filters = {'hidden__exact': 0}
    if todo_only:
        filters['lane'] = None

    fcl = HTSChangeList(request, Library,
                        list_filter=['affiliations', 'library_species'],
                        search_fields=['id', 'library_name', 'amplified_from_sample__id'],
                        list_per_page=200,
                        model_admin=LibraryOptions(Library, admin_site),
                        extra_filters=filters,
                        )

    context = {'cl': fcl,
               "opts": fcl.opts,
               'library_list': fcl.result_list,
               'title': 'Library Index',
               'todo_only': todo_only}

    return render(request, 'samples/library_index.html', context)


def library_not_run(request):
    return library_index(request, todo_only=True)


def library_detail(request, library_id):
    """
    Display information about all the flowcells a library has been run on.
    """
    library = get_object_or_404(Library, id=library_id)

    flowcell_list = []
    flowcell_run_results = {}  # aka flowcells we're looking at
    for lane in library.lane_set.all():
        fc = lane.flowcell
        flowcell_id, id = parse_flowcell_id(fc.flowcell_id)
        if flowcell_id not in flowcell_run_results:
            flowcell_run_results[flowcell_id] = get_flowcell_result_dict(flowcell_id)
        flowcell_list.append((fc.flowcell_id, lane.lane_number))

    flowcell_list.sort()
    lane_summary_list = []
    eland_results = []
    for fc, lane_number in flowcell_list:
        lane_summary, err_list = _summary_stats(fc, lane_number, library_id)
        lane_summary_list.extend(lane_summary)

        eland_results.extend(_make_eland_results(fc, lane_number, flowcell_run_results))

    context = {
        'page_name': 'Library Details',
        'lib': library,
        'eland_results': eland_results,
        'lane_summary_list': lane_summary_list,
    }
    context.update(SAMPLES_CONTEXT_DEFAULTS)

    return render(request, 'samples/library_detail.html', context)


def summaryhtm_fc_cnm(request, flowcell_id, cnm):
    """
    returns a Summary.htm file if it exists.
    """
    fc_id, status = parse_flowcell_id(flowcell_id)
    d = get_flowcell_result_dict(fc_id)

    if d is None:
        return HttpResponse('<b>Results for Flowcell %s not found.</b>' % (fc_id))

    if cnm not in d:
        return HttpResponse('<b>Results for Flowcell %s; %s not found.</b>' % (fc_id, cnm))

    summary_filepath = d[cnm]['summary']

    if summary_filepath is None:
        return HttpResponse('<b>Summary.htm for Flowcell %s; %s not found.</b>' % (fc_id, cnm))

    f = open(summary_filepath, 'r')

    return HttpResponse(f)


def result_fc_cnm_eland_lane(request, flowcell_id, cnm, lane):
    """
    returns an eland_file upon calling.
    """
    fc_id, status = parse_flowcell_id(flowcell_id)
    d = get_flowcell_result_dict(fc_id)

    if d is None:
        return HttpResponse('<b>Results for Flowcell %s not found.</b>' % (fc_id))

    if cnm not in d:
        return HttpResponse('<b>Results for Flowcell %s; %s not found.</b>' % (fc_id, cnm))

    erd = d[cnm]['eland_results']
    lane = int(lane)

    if lane not in erd:
        return HttpResponse('<b>Results for Flowcell %s; %s; lane %s not found.</b>' % (fc_id, cnm, lane))

    filepath = erd[lane]

    #f = opener.autoopen(filepath, 'r')
    # return HttpResponse(f, content_type="application/x-elandresult")

    f = open(filepath, 'r')
    return HttpResponse(f, content_type='application/x-bzip2')


def bedfile_fc_cnm_eland_lane_ucsc(request, fc_id, cnm, lane):
    """
    returns a bed file for a given flowcell, CN-M (i.e. C1-33), and lane (ucsc compatible)
    """
    return bedfile_fc_cnm_eland_lane(request, fc_id, cnm, lane, ucsc_compatible=True)


def bedfile_fc_cnm_eland_lane(request, flowcell_id, cnm, lane, ucsc_compatible=False):
    """
    returns a bed file for a given flowcell, CN-M (i.e. C1-33), and lane
    """
    fc_id, status = parse_flowcell_id(flowcell_id)
    d = get_flowcell_result_dict(fc_id)

    if d is None:
        return HttpResponse('<b>Results for Flowcell %s not found.</b>' % (fc_id))

    if cnm not in d:
        return HttpResponse('<b>Results for Flowcell %s; %s not found.</b>' % (fc_id, cnm))

    erd = d[cnm]['eland_results']
    lane = int(lane)

    if lane not in erd:
        return HttpResponse('<b>Results for Flowcell %s; %s; lane %s not found.</b>' % (fc_id, cnm, lane))

    filepath = erd[lane]

    # Eland result file
    fi = opener.autoopen(filepath, 'r')
    # output memory file

    name, description = makebed.make_description(fc_id, lane)

    bedgen = makebed.make_bed_from_eland_generator(fi, name, description)

    if ucsc_compatible:
        return HttpResponse(bedgen)
    else:
        return HttpResponse(bedgen, content_type="application/x-bedfile")


def _summary_stats(flowcell_id, lane_id, library_id):
    """
    Return the summary statistics for a given flowcell, lane, and end.
    """
    fc_id, status = parse_flowcell_id(flowcell_id)
    fc_result_dict = get_flowcell_result_dict(fc_id)

    summary_list = []
    err_list = []

    if fc_result_dict is None:
        err_list.append('Results for Flowcell %s not found.' % (fc_id))
        return (summary_list, err_list)

    for cycle_width in fc_result_dict:
        xmlpath = fc_result_dict[cycle_width]['run_xml']

        if xmlpath is None:
            err_list.append('Run xml for Flowcell %s(%s) not found.' % (fc_id, cycle_width))
            continue

        run = runfolder.load_pipeline_run_xml(xmlpath)
        # skip if we don't have available metadata.
        if run.gerald is None or run.gerald.summary is None:
            continue

        gerald_summary = run.gerald.summary.lane_results
        key = SampleKey(lane=lane_id, sample='s')
        eland_results = list(run.gerald.eland_results.find_keys(key))
        key = SampleKey(lane=lane_id, sample=library_id)
        eland_results.extend(run.gerald.eland_results.find_keys(key))
        for key in eland_results:
            eland_summary = run.gerald.eland_results.results[key]
            # add information to lane_summary
            eland_summary.flowcell_id = flowcell_id

            read = key.read-1 if key.read is not None else 0
            try:
                eland_summary.clusters = gerald_summary[read][key.lane].cluster
            except (IndexError, KeyError) as e:
                eland_summary.clustes = None
            eland_summary.cycle_width = cycle_width
            if hasattr(eland_summary, 'genome_map'):
                eland_summary.summarized_reads = runfolder.summarize_mapped_reads(
                    eland_summary.genome_map,
                    eland_summary.mapped_reads)

            # grab some more information out of the flowcell db
            flowcell = FlowCell.objects.get(flowcell_id=flowcell_id)
            #pm_field = 'lane_%d_pM' % (lane_id)
            lanes = flowcell.lane_set.filter(lane_number=lane_id)
            eland_summary.flowcell = flowcell
            eland_summary.lanes = lanes

            summary_list.append(eland_summary)

        #except Exception as e:
        #    summary_list.append("Summary report needs to be updated.")
        #    LOGGER.error("Exception: " + str(e))

    return (summary_list, err_list)


def get_eland_result_type(pathname):
    """
    Guess the eland result file type from the filename
    """
    path, filename = os.path.split(pathname)
    if 'extended' in filename:
        return 'extended'
    elif 'multi' in filename:
        return 'multi'
    elif 'result' in filename:
        return 'result'
    else:
        return 'unknown'


def _make_eland_results(flowcell_id, lane_number, interesting_flowcells):
    fc_id, status = parse_flowcell_id(flowcell_id)
    cur_fc = interesting_flowcells.get(fc_id, None)
    if cur_fc is None:
        return []

    flowcell = FlowCell.objects.get(flowcell_id=flowcell_id)
    lanes = flowcell.lane_set.filter(lane_number=lane_number)
    # Loop throw storage devices if a result has been archived
    storage_id_list = []
    if cur_fc is not None:
        for lts in flowcell.longtermstorage_set.all():
            for sd in lts.storage_devices.all():
                # Use barcode_id if it exists
                if sd.barcode_id is not None and sd.barcode_id != '':
                    storage_id_list.append(sd.barcode_id)
                # Otherwise use UUID
                else:
                    storage_id_list.append(sd.uuid)

    # Formatting for template use
    if len(storage_id_list) == 0:
        storage_ids = None
    else:
        storage_ids = ', '.join(['<a href="/inventory/%s/">%s</a>' % (s, s) for s in storage_id_list])

    results = []
    for cycle in cur_fc.keys():
        result_path = cur_fc[cycle]['eland_results'].get(lanes[0], None)
        result_link = make_result_link(fc_id, cycle, lanes[0], result_path)
        results.append({'flowcell_id': fc_id,
                        'flowcell': flowcell,
                        'run_date': flowcell.run_date,
                        'cycle': cycle,
                        'lane': lanes[0],
                        'summary_url': make_summary_url(flowcell_id, cycle),
                        'result_url': result_link[0],
                        'result_label': result_link[1],
                        'bed_url': result_link[2],
                        'storage_ids': storage_ids})
    return results


def make_summary_url(flowcell_id, cycle_name):
    url = '/results/%s/%s/summary/' % (flowcell_id, cycle_name)
    return url


def make_result_link(flowcell_id, cycle_name, lane, eland_result_path):
    if eland_result_path is None:
        return ("", "", "")

    result_type = get_eland_result_type(eland_result_path)
    result_url = '/results/%s/%s/eland_result/%s' % (flowcell_id, cycle_name, lane)
    result_label = 'eland %s' % (result_type,)
    bed_url = None
    if result_type == 'result':
        bed_url_pattern = '/results/%s/%s/bedfile/%s'
        bed_url = bed_url_pattern % (flowcell_id, cycle_name, lane)

    return (result_url, result_label, bed_url)


def _files(flowcell_id, lane):
    """
    Sets up available files for download
    """
    lane = int(lane)

    flowcell_id, id = parse_flowcell_id(flowcell_id)
    d = get_flowcell_result_dict(flowcell_id)

    if d is None:
        return ''

    output = []

    # c_name == 'CN-M' (i.e. C1-33)
    for c_name in d:

        if d[c_name]['summary'] is not None:
            output.append('<a href="/results/%s/%s/summary/">summary(%s)</a>' %
                          (flowcell_id, c_name, c_name))

        erd = d[c_name]['eland_results']
        if lane in erd:
            result_type = get_eland_result_type(erd[lane])
            result_url_pattern = '<a href="/results/%s/%s/eland_result/%s">eland %s(%s)</a>'
            output.append(result_url_pattern % (flowcell_id, c_name, lane, result_type, c_name))
            if result_type == 'result':
                bed_url_pattern = '<a href="/results/%s/%s/bedfile/%s">bedfile(%s)</a>'
                output.append(bed_url_pattern % (flowcell_id, c_name, lane, c_name))

    if len(output) == 0:
        return ''

    return '(' + '|'.join(output) + ')'


def library_id_to_admin_url(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    return HttpResponseRedirect('/admin/samples/library/%s' % (library.id,))


def library_dict(library_id):
    """
    Given a library id construct a dictionary containing important information
    return None if nothing was found
    """
    try:
        library = Library.objects.get(id=library_id)
    except Library.DoesNotExist:
        return None

    lane_info = []
    for lane in library.lane_set.all():
        lane_info.append({'flowcell': lane.flowcell.flowcell_id,
                          'lane_number': lane.lane_number,
                          'lane_id': lane.id,
                          'paired_end': lane.flowcell.paired_end,
                          'read_length': lane.flowcell.read_length,
                          'status_code': lane.status,
                          'status': LANE_STATUS_MAP[lane.status]})

    info = {
        # 'affiliations'?
        # 'aligned_reads': library.aligned_reads,
        #'amplified_into_sample': library.amplified_into_sample, # into is a colleciton...
        #'amplified_from_sample_id': library.amplified_from_sample,
        #'antibody_name': library.antibody_name(), # we have no antibodies.
        'antibody_id': library.antibody_id,
        'cell_line_id': library.cell_line_id,
        'cell_line': str_or_none(library.cell_line),
        'experiment_type': library.experiment_type.name,
        'experiment_type_id': library.experiment_type_id,
        'gel_cut_size': library.gel_cut_size,
        'hidden': library.hidden,
        'id': library.id,
        'insert_size': library.insert_size,
        'lane_set': lane_info,
        'library_id': library.id,
        'library_name': library.library_name,
        'library_species': library.library_species.scientific_name,
        'library_species_id': library.library_species_id,
        #'library_type': library.library_type.name,
        'library_type_id': library.library_type_id,
        'made_for': library.made_for,
        'made_by': library.made_by,
        'multiplex_index': library.index_sequence_text(),
        'notes': library.notes,
        'replicate': library.replicate,
        'stopping_point': library.stopping_point,
        'successful_pM': str_or_none(library.successful_pM),
        'undiluted_concentration': str_or_none(library.undiluted_concentration)
        }
    if library.library_type_id is None:
        info['library_type'] = None
    else:
        info['library_type'] = library.library_type.name
    return info


@csrf_exempt
def library_json(request, library_id):
    """
    Return a json formatted library dictionary
    """
    require_api_key(request)
    # what validation should we do on library_id?

    library = library_dict(library_id)
    if library is None:
        raise Http404

    return JsonResponse({'result': library})


@csrf_exempt
def species_json(request, species_id):
    """
    Return information about a species.
    """
    raise Http404


def species(request, species_id):
    species = get_object_or_404(Species, id=species_id)

    context = {'species': species}

    return render(request, "samples/species_detail.html", context)


def antibodies(request):
    context = {'antibodies': Antibody.objects.order_by('antigene')}
    return render(request, "samples/antibody_index.html", context)


@login_required
def user_profile(request):
    """
    Information about the user
    """
    context = {
        'page_name': 'User Profile',
        'media': '',
        # 'bcmagic': BarcodeMagicForm(),
        # 'select': 'settings',
    }
    context.update(SAMPLES_CONTEXT_DEFAULTS)
    return render(requst, 'registration/profile.html', context)
