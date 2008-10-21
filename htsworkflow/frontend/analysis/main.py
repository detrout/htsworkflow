# some core functions of analysis manager module
from django.http import HttpResponse
from datetime import datetime
from string import *
import re
from htswfrontend import settings
from htswfrontend.analys_track.models import Task, Project
from django.core.exceptions import ObjectDoesNotExist

def updStatus(request):
    ClIP = request.META['REMOTE_ADDR']
    #Check client access permission                                                                                                                                       
    granted = False
    if (settings.ALLOWED_ANALYS_IPS.has_key(ClIP)):  granted = True
    if not granted: return HttpResponse("access denied.")

    output=''
    taskid=-1;
    # Check required param
    if request.has_key('taskid'): taskid = request['taskid']
    else:  return HttpResponse('missing param task id')

    try:
      rec = Task.objects.get(id=taskid)
      mytimestamp = datetime.now().__str__()
      mytimestamp = re.sub(pattern=":[^:]*$",repl="",string=mytimestamp)
      if request.has_key('msg'):
        rec.task_status += ", "+request['msg']+" ("+mytimestamp+")"
      else :
        rec.task_status = "Registered ("+mytimestamp+")"
      rec.save()
      output = "Hello "+settings.ALLOWED_ANALYS_IPS[ClIP]+". Updated status for task "+taskid
    except ObjectDoesNotExist:
      output = "entry not found: taskid="+taskid

    return HttpResponse(output)
    
      
def getProjects(request):
    ClIP = request.META['REMOTE_ADDR']
    #Check client access permission 
    granted = False
    if (settings.ALLOWED_ANALYS_IPS.has_key(ClIP)):  granted = True
    if not granted: return HttpResponse("access denied.")

    outputfile = ''
    
    All=False
    if (request.has_key('mode')):
      if request['mode']=='all':
        All=True

    try:                                                                                   
      if(All):
        rec = Project.objects.all().distinct()
      else:
        rec = Project.objects.filter(tasks__task_status__exact='defined').distinct()
      
      outputfile = '<?xml version="1.0" ?>'
      outputfile += '\n<Projects Client="'+settings.ALLOWED_ANALYS_IPS[ClIP]+'">'
      for p in rec:
        outputfile += '\n'
        outputfile += '\n<Project ProjectId="'+p.id.__str__()+'" Name="'+p.project_name+'">'
        prj_tasks = p.tasks.all()
        for t in prj_tasks:
          outputfile += '\n'
          if (t.apply_calc == 'QuEST' or t.apply_calc == 'WingPeaks' or t.apply_calc == 'MACS'):
            outputfile += '\n<PeakCalling TaskId="'+t.id.__str__()+'" Name="'+t.task_name+'" Caller="'+t.apply_calc+'" Genome="'+t.subject1.library_species.use_genome_build+'">'
            outputfile += '\n<Signal Library="'+t.subject1.library_id+'"/>'
            outputfile += '\n<Background Library="'+t.subject2.library_id+'"/>'
            outputfile += '\n</PeakCalling>'

          if (t.apply_calc == 'ProfileReads' or t.apply_calc == 'qPCR'):
            outputfile += '\n<'+t.apply_calc+' TaskId="'+t.id.__str__()+'" Name="'+t.task_name+'" Genome="'+t.subject1.library_species.use_genome_build+'" Library="'+t.subject1.library_id+'"/>'

          if (t.apply_calc == 'CompareLibs'):
            outputfile += '\n<CompareLibraries TaskId="'+t.id.__str__()+'" TF="'+t.task_name+'" Genome="'+t.subject1.library_species.use_genome_build+'">'
            outputfile += '\n<Library Library="'+t.subject1.library_id+'"/>'
            outputfile += '\n<Library Library="'+t.subject2.library_id+'"/>'
            outputfile += '\n</CompareLibraries>'

          #if (t.apply_calc == 'ComparePeakCalls'):                                                                                                                            
          # <ComparePeakCalls Genome="hg18" Caller1="QuEST" Set1="A549 GR Dex ChIP" Caller2="QuEST" Set2="A549 GR EtOH ChIP" />                                                
          # outputfile += '\n<ComparePeakCalls TaskId='+t.id.__str__()+' Genome="'+t.subject1.library_species.use_genome_build+'" Caller1="'+t.pcaller1+'" Caller1="'+t.pcaller1+'" Caller2="'+t.pcaller2+'" Set1="'+t.set1+'" Set1="'+t.set2+'"/>' 
          # TO DO: Define these new fields in Task: PCaller1 (QuEST,WingPeaks), PCaller2, Set1(FK to self), Set2 (FK..) ALL NULL=TRUE                                  
        outputfile += '\n</Project>'
      outputfile += '\n</Projects>'
    except ObjectDoesNotExist:
      outputfile = "<?xml version='1.0' ?><Projects></Projects>"

    return HttpResponse(outputfile, mimetype='text/plain')
