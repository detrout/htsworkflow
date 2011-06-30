# some core functions of analysis manager module

from datetime import datetime
from string import *
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from htsworkflow.frontend.analysis.models import Task, Project

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
            if t.subject1:
              outputfile += '\n<Signal Library="'+t.subject1.id+'"/>'
              if t.subject2:
                outputfile += '\n<Background Library="'+t.subject2.id+'"/>'
              else:
                outputfile += '\n<Err>Background Library Missing</Err>'
            else:
              outputfile += '\n<Err>Signal Library Missing</Err>'
            outputfile += '\n<params>'+t.task_params.__str__()+'</params>'
            outputfile += '\n</PeakCalling>'
          
          if (t.apply_calc == 'Methylseq'):
            outputfile += '\n<Methylseq TaskId="'+t.id.__str__()+'" Name="'+t.task_name+'" Genome="'+t.subject1.library_species.use_genome_build+'">'
            if t.subject1:
              outputfile += '\n<Hpa2 Library="'+t.subject1.id+'"/>'
              if t.subject2:
                outputfile += '\n<Msp1 Library="'+t.subject2.id+'"/>'
              else:
                outputfile += '\n<Err>Msp1 Library Missing</Err>'
            else:
              outputfile += '\n<Err>Hpa2 Library Missing</Err>'
            outputfile += '\n<params>'+t.task_params.__str__()+'</params>'
            outputfile += '\n</Methylseq>' 

          if (t.apply_calc == 'ProfileReads' or t.apply_calc == 'qPCR'):
            outputfile += '\n<'+t.apply_calc+' TaskId="'+t.id.__str__()+'" Name="'+t.task_name+'" Genome="'+t.subject1.library_species.use_genome_build+'" Library="'+t.subject1.id+'"/>'

          if (t.apply_calc == 'CompareLibs'):
            outputfile += '\n<CompareLibraries TaskId="'+t.id.__str__()+'" TF="'+t.task_name+'" Genome="'+t.subject1.library_species.use_genome_build+'">'
            if t.subject1:
              outputfile += '\n<Library Library="'+t.subject1.id+'"/>'
            else:
              outputfile += '\n<Err>Library Missing</Err>'
            if t.subject2:
              outputfile += '\n<Library Library="'+t.subject2.id+'"/>'
            else:
              outputfile += '\n<Err>Library Missing</Err>'
            outputfile += '\n<params>'+t.task_params.__str__()+'</params>'
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
