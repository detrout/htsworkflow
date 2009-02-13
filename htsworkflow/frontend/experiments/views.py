# Create your views here.
#from django.template import Context, loader
#shortcut to the above modules
from django.shortcuts import render_to_response, get_object_or_404
from htsworkflow.frontend.experiments.models import *
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

def index(request):
    all_runs = DataRun.objects.order_by('-run_start_time')
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
