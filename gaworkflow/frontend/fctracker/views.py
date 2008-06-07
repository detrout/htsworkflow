# Create your views here.
from gaworkflow.frontend.fctracker.models import Library
from gaworkflow.frontend.fctracker.results import get_flowcell_result_dict, flowcellIdStrip
from gaworkflow.pipeline.runfolder import ElementTree
from gaworkflow.pipeline import runfolder
from gaworkflow.frontend import settings
from gaworkflow.util import makebed
from gaworkflow.util import opener

from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context

import StringIO

#from django.db.models import base 

def library(request):
    library_list = Library.objects.all() #.order_by('-pub_date')
    rep_string = '<a href="/library/%s/">%s - %s (%s)</a>'
    output = '<br />\n'.join([rep_string \
      % (l.library_id,
         l.library_id,
         l.library_name,
         l.library_species.scientific_name) for l in library_list])
    return HttpResponse(output)

def library_to_flowcells(request, lib_id):
    """
    Display information about all the flowcells a library has been run on.
    """
    t = get_template("summary_stats.html")
    
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
    
    output.append('<br />')
    
    data_dict_list = []
    for fc, lane in flowcell_list:
        dicts, err_list = _summary_stats(fc, lane)
        
        data_dict_list.extend(dicts)
    
        for err in err_list:    
            output.append(err)
    
    html = t.render(Context({'data_dict_list': data_dict_list}))
    output.append('<br />')
    output.append('<br />')
    output.append(html)
    output.append('<br />')
    output.append('<br />')
    
    if record_count == 0:
        output.append("None Found")
    
    return HttpResponse('<br />\n'.join(output))


def summaryhtm_fc_cnm(request, fc_id, cnm):
    """
    returns a Summary.htm file if it exists.
    """
    fc_id = flowcellIdStrip(fc_id)
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
    fc_id = flowcellIdStrip(fc_id)
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
    fc_id = flowcellIdStrip(fc_id)
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
    
    
    name, description = makebed.make_description(settings.DATABASE_NAME,
                                                 fc_id,
                                                 lane)
    
    bedgen = makebed.make_bed_from_eland_stream_generator(fi, name, description)
    
    if ucsc_compatible:
        return HttpResponse(bedgen)
    else:
        return HttpResponse(bedgen, mimetype="application/x-bedfile")


def _summary_stats(flowcell_id, lane):
    """
    return a dictionary of summary stats for a given flowcell_id & lane.
    """
    fc_id = flowcellIdStrip(flowcell_id)
    fc_result_dict = get_flowcell_result_dict(fc_id)
    
    dict_list = []
    err_list = []
    
    if fc_result_dict is None:
        err_list.append('Results for Flowcell %s not found.' % (fc_id))
        return (dict_list, err_list)
    
    for cnm in fc_result_dict:
    
        xmlpath = fc_result_dict[cnm]['run_xml']
        
        if xmlpath is None:
            err_list.append('Run xml for Flowcell %s(%s) not found.' % (fc_id, cnm))
            continue
        
        tree = ElementTree.parse(xmlpath).getroot()
        results = runfolder.PipelineRun(pathname='', xml=tree)
        
        lane_results = results.gerald.summary[str(lane)]
        lrs = lane_results
        
        d = {}
        
        d['average_alignment_score'] = lrs.average_alignment_score
        d['average_first_cycle_intensity'] = lrs.average_first_cycle_intensity
        d['cluster'] = lrs.cluster
        d['lane'] = lrs.lane
        d['flowcell'] = flowcell_id
        d['percent_error_rate'] = lrs.percent_error_rate
        d['percent_intensity_after_20_cycles'] = lrs.percent_intensity_after_20_cycles
        d['percent_pass_filter_align'] = lrs.percent_pass_filter_align
        d['percent_pass_filter_clusters'] = lrs.percent_pass_filter_clusters
        
        #FIXME: function finished, but need to take advantage of
        #   may need to take in a list of lanes so we only have to
        #   load the xml file once per flowcell rather than once
        #   per lane.
        dict_list.append(d)
    
    return (dict_list, err_list)
    
    

    
def _files(flowcell_id, lane):
    """
    Sets up available files for download
    """
    flowcell_id = flowcellIdStrip(flowcell_id)
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
            