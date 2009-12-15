# Create your views here.
import StringIO
import logging
import os
import sys

try:
    import json
except ImportError, e:
    import simplejson as json

from htsworkflow.frontend.auth import require_api_key
from htsworkflow.frontend.experiments.models import FlowCell
from htsworkflow.frontend.samples.changelist import ChangeList
from htsworkflow.frontend.samples.models import Library
from htsworkflow.frontend.samples.results import get_flowcell_result_dict, parse_flowcell_id
from htsworkflow.frontend.bcmagic.forms import BarcodeMagicForm
from htsworkflow.pipelines.runfolder import load_pipeline_run_xml
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines.eland import ResultLane
from htsworkflow.frontend import settings
from htsworkflow.util import makebed
from htsworkflow.util import opener

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required

LANE_LIST = [1,2,3,4,5,6,7,8]
SAMPLES_CONTEXT_DEFAULTS = {
    'app_name': 'Flowcell/Library Tracker',
    'bcmagic': BarcodeMagicForm()
}

def create_library_context(cl):
    """
    Create a list of libraries that includes how many lanes were run
    """
    records = []
    #for lib in library_items.object_list:
    for lib in cl.result_list:
       summary = {}
       summary['library_id'] = lib.id
       summary['library_name'] = lib.library_name
       summary['species_name' ] = lib.library_species.scientific_name
       if lib.amplified_from_sample is not None:
           summary['amplified_from'] = lib.amplified_from_sample.id
       else:
           summary['amplified_from'] = ''
       lanes_run = 0
       #for lane_id in LANE_LIST:
       #    lane = getattr(lib, 'lane_%d_library' % (lane_id,))
       #    lanes_run += len( lane.all() )
       lanes_run = lib.lane_set.count()
       summary['lanes_run'] = lanes_run
       summary['is_archived'] = lib.is_archived()
       records.append(summary)
    cl.result_count = unicode(cl.paginator._count) + u" libraries"
    return {'library_list': records }

def library(request):
   # build changelist
    fcl = ChangeList(request, Library,
        list_filter=['affiliations', 'library_species'],
        search_fields=['id', 'library_name', 'amplified_from_sample__id'],
        list_per_page=200,
        queryset=Library.objects.filter(hidden__exact=0)
    )

    context = { 'cl': fcl, 'title': 'Library Index'}
    context.update(create_library_context(fcl))
    t = get_template('samples/library_index.html')
    c = RequestContext(request, context)
    
    app_context = {
        'page_name': 'Library Index',
        'east_region_config_div': 'changelist-filter',
        'body': t.render(c)
    }
    app_context.update(SAMPLES_CONTEXT_DEFAULTS)
    
    app_t = get_template('flowcell_libraries_app.html')
    app_c = RequestContext(request, app_context)
    return HttpResponse( app_t.render(app_c) )

def library_to_flowcells(request, lib_id):
    """
    Display information about all the flowcells a library has been run on.
    """
    
    try:
      lib = Library.objects.get(id=lib_id)
    except:
      return HttpResponse("Library %s does not exist" % (lib_id))
   
    flowcell_list = []
    flowcell_run_results = {} # aka flowcells we're looking at
    for lane in lib.lane_set.all():
        fc = lane.flowcell
        flowcell_id, id = parse_flowcell_id(fc.flowcell_id)
        if flowcell_id not in flowcell_run_results:
            flowcell_run_results[flowcell_id] = get_flowcell_result_dict(flowcell_id)
        flowcell_list.append((fc.flowcell_id, lane.lane_number))

    flowcell_list.sort()
    lane_summary_list = []
    eland_results = []
    for fc, lane_number in flowcell_list:
        lane_summary, err_list = _summary_stats(fc, lane_number)

        eland_results.extend(_make_eland_results(fc, lane_number, flowcell_run_results))
        lane_summary_list.extend(lane_summary)

    context = {
        'page_name': 'Library Details',
        'lib': lib,
        'eland_results': eland_results,
        'lane_summary_list': lane_summary_list,
    }
    context.update(SAMPLES_CONTEXT_DEFAULTS)

    return render_to_response(
        'samples/library_detail.html',
        context,
        context_instance = RequestContext(request))

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
    # return HttpResponse(f, mimetype="application/x-elandresult")

    f = open(filepath, 'r')
    return HttpResponse(f, mimetype='application/x-bzip2')
    


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
    
    name, description = makebed.make_description( fc_id, lane )
    
    bedgen = makebed.make_bed_from_eland_generator(fi, name, description)
    
    if ucsc_compatible:
        return HttpResponse(bedgen)
    else:
        return HttpResponse(bedgen, mimetype="application/x-bedfile")


def _summary_stats(flowcell_id, lane_id):
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
        
        run = load_pipeline_run_xml(xmlpath)
        gerald_summary = run.gerald.summary.lane_results
        for end in range(len(gerald_summary)):
            end_summary = run.gerald.eland_results.results[end]
            if end_summary.has_key(lane_id):
                eland_summary = run.gerald.eland_results.results[end][lane_id]
            else:
                eland_summary = ResultLane(lane_id=lane_id, end=end)
            # add information to lane_summary
            eland_summary.flowcell_id = flowcell_id
            if len(gerald_summary) > end and gerald_summary[end].has_key(lane_id):
                eland_summary.clusters = gerald_summary[end][lane_id].cluster
            else:
                eland_summary.clusters = None
            eland_summary.cycle_width = cycle_width
            if hasattr(eland_summary, 'genome_map'):
                eland_summary.summarized_reads = runfolder.summarize_mapped_reads( 
                                                   eland_summary.genome_map, 
                                                   eland_summary.mapped_reads)

            # grab some more information out of the flowcell db
            flowcell = FlowCell.objects.get(flowcell_id=flowcell_id)
            #pm_field = 'lane_%d_pM' % (lane_id)
            lane_obj = flowcell.lane_set.get(lane_number=lane_id)
            eland_summary.successful_pm = lane_obj.pM

            summary_list.append(eland_summary)

        #except Exception, e:
        #    summary_list.append("Summary report needs to be updated.")
        #    logging.error("Exception: " + str(e))
    
    return (summary_list, err_list)

def _summary_stats_old(flowcell_id, lane):
    """
    return a dictionary of summary stats for a given flowcell_id & lane.
    """
    fc_id, status = parse_flowcell_id(flowcell_id)
    fc_result_dict = get_flowcell_result_dict(fc_id)
    
    dict_list = []
    err_list = []
    summary_list = []
    
    if fc_result_dict is None:
        err_list.append('Results for Flowcell %s not found.' % (fc_id))
        return (dict_list, err_list, summary_list)
    
    for cnm in fc_result_dict:
    
        xmlpath = fc_result_dict[cnm]['run_xml']
        
        if xmlpath is None:
            err_list.append('Run xml for Flowcell %s(%s) not found.' % (fc_id, cnm))
            continue
        
        tree = ElementTree.parse(xmlpath).getroot()
        results = runfolder.PipelineRun(pathname='', xml=tree)
        try:
            lane_report = runfolder.summarize_lane(results.gerald, lane)
            summary_list.append(os.linesep.join(lane_report))
        except Exception, e:
            summary_list.append("Summary report needs to be updated.")
            logging.error("Exception: " + str(e))
       
        print >>sys.stderr, "----------------------------------"
        print >>sys.stderr, "-- DOES NOT SUPPORT PAIRED END ---"
        print >>sys.stderr, "----------------------------------"
        lane_results = results.gerald.summary[0][lane]
        lrs = lane_results
        
        d = {}
        
        d['average_alignment_score'] = lrs.average_alignment_score
        d['average_first_cycle_intensity'] = lrs.average_first_cycle_intensity
        d['cluster'] = lrs.cluster
        d['lane'] = lrs.lane
        d['flowcell'] = flowcell_id
        d['cnm'] = cnm
        d['percent_error_rate'] = lrs.percent_error_rate
        d['percent_intensity_after_20_cycles'] = lrs.percent_intensity_after_20_cycles
        d['percent_pass_filter_align'] = lrs.percent_pass_filter_align
        d['percent_pass_filter_clusters'] = lrs.percent_pass_filter_clusters
        
        #FIXME: function finished, but need to take advantage of
        #   may need to take in a list of lanes so we only have to
        #   load the xml file once per flowcell rather than once
        #   per lane.
        dict_list.append(d)
    
    return (dict_list, err_list, summary_list)
    
    
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

def _make_eland_results(flowcell_id, lane, interesting_flowcells):
    fc_id, status = parse_flowcell_id(flowcell_id)
    cur_fc = interesting_flowcells.get(fc_id, None)
    if cur_fc is None:
      return []

    flowcell = FlowCell.objects.get(flowcell_id=flowcell_id)
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
        storage_ids = ', '.join([ '<a href="/inventory/%s/">%s</a>' % (s,s) for s in storage_id_list ])

    results = []
    for cycle in cur_fc.keys():
        result_path = cur_fc[cycle]['eland_results'].get(lane, None)
        result_link = make_result_link(fc_id, cycle, lane, result_path)
        results.append({'flowcell_id': fc_id,
                        'run_date': flowcell.run_date,
                        'cycle': cycle, 
                        'lane': lane, 
                        'summary_url': make_summary_url(flowcell_id, cycle),
                        'result_url': result_link[0],
                        'result_label': result_link[1],
                        'bed_url': result_link[2],
                        'storage_ids': storage_ids
        })
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
            output.append('<a href="/results/%s/%s/summary/">summary(%s)</a>' \
                          % (flowcell_id, c_name, c_name))
        
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

def library_id_to_admin_url(request, lib_id):
    lib = Library.objects.get(id=lib_id)
    return HttpResponseRedirect('/admin/samples/library/%s' % (lib.id,))

def library_dict(library_id):
    """
    Given a library id construct a dictionary containing important information
    return None if nothing was found
    """
    try:
        lib = Library.objects.get(id = library_id)
    except Library.DoesNotExist, e:
        return None

    #lane_info = lane_information(lib.lane_set)
    lane_info = []
    for lane in lib.lane_set.all():
        lane_info.append( {'flowcell':lane.flowcell.flowcell_id,
                           'lane_number': lane.lane_number} )
        
    info = {
        # 'affiliations'?
        # 'aligned_reads': lib.aligned_reads,
        #'amplified_into_sample': lib.amplified_into_sample, # into is a colleciton...
        #'amplified_from_sample_id': lib.amplified_from_sample, 
        #'antibody_name': lib.antibody_name(), # we have no antibodies.
        'antibody_id': lib.antibody_id,
        'avg_lib_size': lib.avg_lib_size,
        'cell_line': lib.cell_line.cellline_name,
        'cell_line_id': lib.cell_line_id,
        'experiment_type': lib.experiment_type.name,
        'experiment_type_id': lib.experiment_type_id,
        'id': lib.id,
        'lane_set': lane_info,
        'library_id': lib.id,
        'library_name': lib.library_name,
        'library_species': lib.library_species.scientific_name,
        'library_species_id': lib.library_species_id,
        #'library_type': lib.library_type.name,
        'library_type_id': lib.library_type_id,
        'made_for': lib.made_for,
        'made_by': lib.made_by,
        'notes': lib.notes,
        'replicate': lib.replicate,
        'stopping_point': lib.stopping_point,
        'successful_pM': unicode(lib.successful_pM),
        'undiluted_concentration': unicode(lib.undiluted_concentration)
        }
    if lib.library_type_id is None:
        info['library_type'] = None
    else:
        info['library_type'] = lib.library_type.name
    return info

def library_json(request, library_id):
    """
    Return a json formatted library dictionary
    """
    require_api_key(request)
    # what validation should we do on library_id?
    
    lib = library_dict(library_id)
    if lib is None:
        raise Http404

    lib_json = json.dumps(lib)
    return HttpResponse(lib_json, mimetype='application/json')

def species_json(request, species_id):
    """
    Return information about a species.
    """
    raise Http404
    
@login_required
def user_profile(request):
    """
    Information about the user
    """
    context = {
                'page_name': 'User Profile',
                'media': '',
                #'bcmagic': BarcodeMagicForm(),
                #'select': 'settings',
            }
    context.update(SAMPLES_CONTEXT_DEFAULTS)
    return render_to_response('registration/profile.html', context,
                              context_instance=RequestContext(request))

