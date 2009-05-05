# Create your views here.
from htsworkflow.frontend.experiments.models import FlowCell
from htsworkflow.frontend.samples.changelist import ChangeList
from htsworkflow.frontend.samples.models import Library
from htsworkflow.frontend.samples.results import get_flowcell_result_dict, parse_flowcell_id
from htsworkflow.pipelines.runfolder import load_pipeline_run_xml
from htsworkflow.pipelines import runfolder
from htsworkflow.frontend import settings
from htsworkflow.util import makebed
from htsworkflow.util import opener

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template

import StringIO
import logging
import os

LANE_LIST = [1,2,3,4,5,6,7,8]

def create_library_context(cl):
    """
    Create a list of libraries that includes how many lanes were run
    """
    records = []
    #for lib in library_items.object_list:
    for lib in cl.result_list:
       summary = {}
       summary['library_id'] = lib.library_id
       summary['library_name'] = lib.library_name
       summary['species_name' ] = lib.library_species.scientific_name
       if lib.amplified_from_sample is not None:
           summary['amplified_from'] = lib.amplified_from_sample.library_id
       else:
           summary['amplified_from'] = ''
       lanes_run = 0
       for lane_id in LANE_LIST:
           lane = getattr(lib, 'lane_%d_library' % (lane_id,))
           lanes_run += len( lane.all() )
       summary['lanes_run'] = lanes_run
       records.append(summary)
    cl.result_count = unicode(cl.paginator._count) + u" libraries"
    return {'library_list': records }

def library(request):
   # build changelist
    fcl = ChangeList(request, Library,
        list_filter=['affiliations', 'library_species'],
        search_fields=['library_id', 'library_name', 'amplified_from_sample__library_id'],
        list_per_page=200,
        queryset=Library.objects.filter(hidden__exact=0)
    )

    context = { 'cl': fcl, 'title': 'Library Index'}
    context.update(create_library_context(fcl))
    t = get_template('samples/library_index.html')
    c = RequestContext(request, context)
    return HttpResponse( t.render(c) )

def library_to_flowcells(request, lib_id):
    """
    Display information about all the flowcells a library has been run on.
    """
    
    try:
      lib = Library.objects.get(library_id=lib_id)
    except:
      return HttpResponse("Library %s does not exist" % (lib_id))
   
    flowcell_list = []
    interesting_flowcells = {} # aka flowcells we're looking at
    for lane in LANE_LIST:
        lane_library = getattr(lib, 'lane_%d_library' % (lane,))
        for fc in lane_library.all():
            flowcell_id, id = parse_flowcell_id(fc.flowcell_id)
            if flowcell_id not in interesting_flowcells:
                interesting_flowcells[flowcell_id] = get_flowcell_result_dict(flowcell_id)
            flowcell_list.append((fc.flowcell_id, lane))

    flowcell_list.sort()
    
    lane_summary_list = []
    eland_results = []
    for fc, lane in flowcell_list:
        lane_summary, err_list = _summary_stats(fc, lane)
        
        eland_results.extend(_make_eland_results(fc, lane, interesting_flowcells))
        lane_summary_list.extend(lane_summary)


    return render_to_response(
        'samples/library_detail.html',
        {'lib': lib,
         'eland_results': eland_results,
         'lane_summary_list': lane_summary_list,
        },
        context_instance = RequestContext(request))

def summaryhtm_fc_cnm(request, fc_id, cnm):
    """
    returns a Summary.htm file if it exists.
    """
    fc_id, status = parse_flowcell_id(fc_id)
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


def result_fc_cnm_eland_lane(request, fc_id, cnm, lane):
    """
    returns an eland_file upon calling.
    """
    fc_id, status = parse_flowcell_id(fc_id)
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


def bedfile_fc_cnm_eland_lane(request, fc_id, cnm, lane, ucsc_compatible=False):
    """
    returns a bed file for a given flowcell, CN-M (i.e. C1-33), and lane
    """
    fc_id, status = parse_flowcell_id(fc_id)
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
        
        try:
            run = load_pipeline_run_xml(xmlpath)
            gerald_summary = run.gerald.summary.lane_results
            for end in range(len(gerald_summary)):
                eland_summary = run.gerald.eland_results.results[end][lane_id]
                # add information to lane_summary
                eland_summary.flowcell_id = flowcell_id
                eland_summary.clusters = gerald_summary[end][lane_id].cluster
                eland_summary.cycle_width = cycle_width
		if hasattr(eland_summary, 'genome_map'):
                    eland_summary.summarized_reads = runfolder.summarize_mapped_reads( 
                                                       eland_summary.genome_map, 
                                                       eland_summary.mapped_reads)

                # grab some more information out of the flowcell db
                flowcell = FlowCell.objects.get(flowcell_id=fc_id)
                pm_field = 'lane_%d_pM' % (lane_id)
                eland_summary.successful_pm = getattr(flowcell, pm_field)

                summary_list.append(eland_summary)

        except Exception, e:
            summary_list.append("Summary report needs to be updated.")
            logging.error("Exception: " + str(e))
    
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
       
        print "----------------------------------"
        print "-- DOES NOT SUPPORT PAIRED END ---"
        print "----------------------------------"
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

    cur_fc = interesting_flowcells.get(flowcell_id, None)
    if cur_fc is None:
      return []

    results = []
    for cycle in cur_fc.keys():
        result_path = cur_fc[cycle]['eland_results'].get(lane, None)
        result_link = make_result_link(flowcell_id, cycle, lane, result_path)
        results.append({'flowcell_id': flowcell_id,
                        'cycle': cycle, 
                        'lane': lane, 
                        'summary_url': make_summary_url(flowcell_id, cycle),
                        'result_url': result_link[0],
                        'result_label': result_link[1],
                        'bed_url': result_link[2],
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
    lib = Library.objects.get(library_id=lib_id)
    return HttpResponseRedirect('/admin/samples/library/%s' % (lib.id,))

