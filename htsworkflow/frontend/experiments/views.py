# Create your views here.
#from django.template import Context, loader
#shortcut to the above modules
from django.shortcuts import render_to_response, get_object_or_404
#from htswfrontend.fctracker.models import *
from htsworkflow.frontend.experiments.models import *
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

def index(request):
    all_runs = DataRun.objects.all().order_by('-run_start_time')
    #t = loader.get_template('experiments/index.html')
    #c = Context({
    #    'data_run_list': all_runs,
    #})
    #return HttpResponse(t.render(c)) 
    # shortcut to the above module usage
    return render_to_response('experiments/index.html',{'data_run_list': all_runs}) 
    
def detail(request, run_folder):
    html_str = '<h2>Exp Track Details Page</h2>'
    html_str += 'Run Folder: '+run_folder
    r = get_object_or_404(DataRun,run_folder=run_folder)
    return render_to_response('experiments/detail.html',{'run_f': r})

def makeFCSheet(request,fcid):
  # get Flowcell by input fcid
  # ...
  rec = None
  try:
    rec = FlowCell.objects.get(flowcell_id=fcid)
  except ObjectDoesNotExist:
    pass
  lanes = ['1','2','3','4','5','6','7','8']
  return render_to_response('experiments/flowcellSheet.html',{'fc': rec})

def test_Libs(request):
  str = ''
  str += '<table border=1><tr><th>Lib ID</th><th>Current Libaray Name (Free Text)</th><th>Auto-composed Libaray Name (antibody + celline + libid + species + [replicate])</th></tr>'
  allLibs = Library.objects.all()
  #allLibs = Library.objects.filter(antibody__isnull=False)
  for L in allLibs:
    str += '<tr>'
    str += '<td>'+L.library_id+'</td><td>'+L.library_name+'</td>'   
    str += '<td>'
    str += L.experiment_type+'_'
    if L.cell_line.cellline_name != 'Unknown':
      str += L.cell_line.cellline_name+'_'

    try:
      if L.antibody is not None:
        str += L.antibody.nickname + '_'
    except Antibody.DoesNotExist:
      pass
  
    str += 'Rep'+L.replicate.__str__()
    str += '</td></tr>' 

  str += '</table>'
  return HttpResponse(str)  
