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

from django.http import HttpResponse
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
        list_filter=['library_species','affiliations'],
        search_fields=['library_id', 'library_name'],
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
    t = get_template("samples/library_detail.html")
    
    try:
      lib = Library.objects.get(library_id=lib_id)
    except:
      return HttpResponse("Library %s does not exist" % (lib_id))
    
    output = []
    
    output.append('<b>Library ID:</b> %s' % (lib.library_id))
    output.append('<b>Name:</b> %s' % (lib.library_name))
    output.append('<b>Species:</b> %s' % (lib.library_species.scientific_name))
    output.append('')
    
    output.append('<b>FLOWCELL - LANE:</b>')
    
    output.extend([ '%s - Lane 1 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 1)) for fc in lib.lane_1_library.all() ])
    output.extend([ '%s - Lane 2 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 2)) for fc in lib.lane_2_library.all() ])
    output.extend([ '%s - Lane 3 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 3)) for fc in lib.lane_3_library.all() ])
    output.extend([ '%s - Lane 4 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 4)) for fc in lib.lane_4_library.all() ])
    output.extend([ '%s - Lane 5 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 5)) for fc in lib.lane_5_library.all() ])
    output.extend([ '%s - Lane 6 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 6)) for fc in lib.lane_6_library.all() ])
    output.extend([ '%s - Lane 7 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 7)) for fc in lib.lane_7_library.all() ])
    output.extend([ '%s - Lane 8 %s' % (fc.flowcell_id, _files(fc.flowcell_id, 8)) for fc in lib.lane_8_library.all() ])
    
    record_count = lib.lane_1_library.count() + \
                    lib.lane_2_library.count() + \
                    lib.lane_3_library.count() + \
                    lib.lane_4_library.count() + \
                    lib.lane_5_library.count() + \
                    lib.lane_6_library.count() + \
                    lib.lane_7_library.count() + \
                    lib.lane_8_library.count()
    
    flowcell_list = []
    flowcell_list.extend([ (fc.flowcell_id, 1) for fc in lib.lane_1_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 2) for fc in lib.lane_2_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 3) for fc in lib.lane_3_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 4) for fc in lib.lane_4_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 5) for fc in lib.lane_5_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 6) for fc in lib.lane_6_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 7) for fc in lib.lane_7_library.all() ])
    flowcell_list.extend([ (fc.flowcell_id, 8) for fc in lib.lane_8_library.all() ])
    flowcell_list.sort()
    
    lane_summary_list = []
    for fc, lane in flowcell_list:
        lane_summary, err_list = _summary_stats(fc, lane)
        
        lane_summary_list.extend(lane_summary)
    
        for err in err_list:    
            output.append(err)
   
    output.append('<br />')
    output.append(t.render(RequestContext(request, {'lane_summary_list': lane_summary_list})))
    output.append('<br />')
    
    if record_count == 0:
        output.append("None Found")
    
    return HttpResponse('<br />\n'.join(output))


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
    
    f = opener.autoopen(filepath, 'r')
    
    return HttpResponse(f, mimetype="application/x-elandresult")


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
                eland_summary.summarized_reads = runfolder.summarize_mapped_reads(eland_summary.mapped_reads)

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
    
    

    
def _files(flowcell_id, lane):
    """
    Sets up available files for download
    """
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
        
        if int(lane) in erd:
            output.append('<a href="/results/%s/%s/eland_result/%s">eland_result(%s)</a>' % (flowcell_id, c_name, lane, c_name))
            output.append('<a href="/results/%s/%s/bedfile/%s">bedfile(%s)</a>' % (flowcell_id, c_name, lane, c_name))
    
    if len(output) == 0:
        return ''
    
    return '(' + '|'.join(output) + ')'
            
