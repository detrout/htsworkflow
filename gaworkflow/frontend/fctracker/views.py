# Create your views here.
from gaworkflow.frontend.fctracker.models import Library
from django.http import HttpResponse

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
    
    output.extend([ '%s - Lane 1' % (fc.flowcell_id) for fc in lib.lane_1_library.all() ])
    output.extend([ '%s - Lane 2' % (fc.flowcell_id) for fc in lib.lane_2_library.all() ])
    output.extend([ '%s - Lane 3' % (fc.flowcell_id) for fc in lib.lane_3_library.all() ])
    output.extend([ '%s - Lane 4' % (fc.flowcell_id) for fc in lib.lane_4_library.all() ])
    output.extend([ '%s - Lane 5' % (fc.flowcell_id) for fc in lib.lane_5_library.all() ])
    output.extend([ '%s - Lane 6' % (fc.flowcell_id) for fc in lib.lane_6_library.all() ])
    output.extend([ '%s - Lane 7' % (fc.flowcell_id) for fc in lib.lane_7_library.all() ])
    output.extend([ '%s - Lane 8' % (fc.flowcell_id) for fc in lib.lane_8_library.all() ])
    
    return HttpResponse('<br />\n'.join(output))
