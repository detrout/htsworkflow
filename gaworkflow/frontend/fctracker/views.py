# Create your views here.
from gaworkflow.frontend.fctracker.models import Library
from gaworkflow.frontend.fctracker.results import get_flowcell_result_dict, flowcellIdStrip
from gaworkflow.frontend import settings
from gaworkflow.util import makebed
from gaworkflow.util import opener
from django.http import HttpResponse

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
    
    if record_count == 0:
        output.append("None Found")
    
    return HttpResponse('<br />\n'.join(output))


def result_fc_cnm_eland_lane(request, fc_id, cnm, lane):
    """
    returns an eland_file upon calling.
    """
    fc_id = flowcellIdStrip(fc_id)
    d = get_flowcell_result_dict(fc_id)
    
    if d is None:
        return HttpResponse('<b>Results for Flowcell %s not found.' % (fc_id))
    
    if cnm not in d:
        return HttpResponse('<b>Results for Flowcell %s; %s not found.' % (fc_id, cnm))
    
    erd = d[cnm]['eland_results']
    lane = int(lane)
    
    if lane not in erd:
        return HttpResponse('<b>Results for Flowcell %s; %s; lane %s not found.' % (fc_id, cnm, lane))
    
    filepath = erd[lane]
    
    f = opener.autoopen(filepath, 'r')
    
    return HttpResponse(f)


def bedfile_fc_cnm_eland_lane(request, fc_id, cnm, lane):
    """
    returns a bed file for a given flowcell, CN-M (i.e. C1-33), and lane
    """
    fc_id = flowcellIdStrip(fc_id)
    d = get_flowcell_result_dict(fc_id)
    
    if d is None:
        return HttpResponse('<b>Results for Flowcell %s not found.' % (fc_id))
    
    if cnm not in d:
        return HttpResponse('<b>Results for Flowcell %s; %s not found.' % (fc_id, cnm))
    
    erd = d[cnm]['eland_results']
    lane = int(lane)
    
    if lane not in erd:
        return HttpResponse('<b>Results for Flowcell %s; %s; lane %s not found.' % (fc_id, cnm, lane))
    
    filepath = erd[lane]
    
    # Eland result file
    fi = open(filepath, 'r')
    # output memory file
    
    
    name, description = makebed.make_description(settings.DATABASE_NAME,
                                                 fc_id,
                                                 lane)
    
    bedgen = makebed.make_bed_from_eland_stream_generator(fi, name, description)
    
    return HttpResponse(bedgen)

    
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
        erd = d[c_name]['eland_results']
        
        if int(lane) in erd:
            output.append('<a href="/results/%s/%s/eland_result/%s">eland_result(%s)</a>' % (flowcell_id, c_name, lane, c_name))
            output.append('<a href="/results/%s/%s/bedfile/%s">bedfile(%s)</a>' % (flowcell_id, c_name, lane, c_name))
    
    if len(output) == 0:
        return ''
    
    return '(' + '|'.join(output) + ')'
            