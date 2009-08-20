# some core functions of the exp tracker module
from datetime import datetime, timedelta
import os
import re

from django.http import HttpResponse
from htsworkflow.frontend import settings
from htsworkflow.frontend.experiments.models import FlowCell, DataRun
from htsworkflow.frontend.samples.models import Library
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, mail_admins

def updStatus(request):
    output=''
    user = 'none'
    pswd = ''
    UpdatedStatus = 'unknown'
    fcid = 'none'
    runfolder = 'unknown'
    ClIP = request.META['REMOTE_ADDR']

    if hasattr(request, 'user'):
      user = request.user

    #Check access permission
    if not (user.is_superuser and settings.ALLOWED_IPS.has_key(ClIP)): 
        return HttpResponse("%s access denied from %s." % (user, ClIP))

    # ~~~~~~Parameters for the job ~~~~
    if request.REQUEST.has_key('fcid'):
      fcid = request.REQUEST['fcid']
    else:
      return HttpResponse('missing fcid')
    
    if request.REQUEST.has_key('runf'):
      runfolder = request.REQUEST['runf']
    else:
      return HttpResponse('missing runf')

    
    if request.REQUEST.has_key('updst'):
      UpdatedStatus = request.REQUEST['updst']
    else:
      return HttpResponse('missing status')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

    # Update Data Run status in DB
    # Try get rec. If not found return 'entry not found + <fcid><runfolder>', if found try update and return updated 
    try:
      rec = DataRun.objects.get(run_folder=runfolder)
      rec.run_status = UpdatedStatus

      #if there's a message update that too
      mytimestamp = datetime.now().__str__()
      mytimestamp = re.sub(pattern=":[^:]*$",repl="",string=mytimestamp)
      if request.REQUEST.has_key('msg'):
        rec.run_note += ", "+request.REQUEST['msg']+" ("+mytimestamp+")"
      else :
        if UpdatedStatus == '1':
          rec.run_note = "Started ("+mytimestamp+")"

      rec.save()
      output = "Hello "+settings.ALLOWED_IPS[ClIP]+". Updated to:'"+DataRun.RUN_STATUS_CHOICES[int(UpdatedStatus)][1].__str__()+"'"
    except ObjectDoesNotExist:
      output = "entry not found: "+fcid+", "+runfolder


    #Notify researcher by email
    # Doesn't work
    #send_mail('Exp Tracker', 'Data Run Status '+output, 'rrauch@stanford.edu', ['rrrami@gmail.com'], fail_silently=False)
    #mail_admins("test subject", "testing , testing", fail_silently=False)
    # gives error: (49, "Can't assign requested address")
    return HttpResponse(output)

def generateConfile(request,fcid):
    #granted = False
    #ClIP = request.META['REMOTE_ADDR']
    #if (settings.ALLOWED_IPS.has_key(ClIP)):  granted = True

    #if not granted: return HttpResponse("access denied.")

    config = ['READ_LENGTH 25']
    config += ['ANALYSIS eland']
    config += ['GENOME_FILE all_chr.fa']
    config += ['ELAND_MULTIPLE_INSTANCES 8']
    genome_dir = 'GENOME_DIR /Volumes/Genomes/'
    eland_genome = 'ELAND_GENOME /Volumes/Genomes/'
    
    try:                                                                                                                                              
      fc = FlowCell.objects.get(flowcell_id=fcid)
      for lane in fc.lane_set.all():
          print dir(lane.library.library_species)
          config += [ str(lane.lane_number) +":" + \
                      genome_dir + lane.library.library_species.scientific_name ]
          config += [ str(lane.lane_number) +":" + \
                      eland_genome + lane.library.library_species.scientific_name ]
      
    except ObjectDoesNotExist:
      config = 'Entry not found for fcid  = '+fcid

    return os.linesep.join(config)

def getConfile(req):
    granted = False
    ClIP = req.META['REMOTE_ADDR']
    if (settings.ALLOWED_IPS.has_key(ClIP)):  granted = True

    if not granted: return HttpResponse("access denied. IP: "+ClIP)

    fcid = 'none'
    cnfgfile = 'Nothing found'
    runfolder = 'unknown'
    request = req.REQUEST
    print request, dir(request)
    print request['fcid'], request.has_key('fcid')
    print request['runf']
    if request.has_key('fcid'):
      fcid = request['fcid']
      if request.has_key('runf'):
        runfolder = request['runf']
        try:
          rec = DataRun.objects.get(run_folder=runfolder) #,flowcell_id=fcid)
          cnfgfile = rec.config_params
          #match_str = re.compile(r"READ_LENGTH.+$")
          match_str = re.compile('^READ_LENGTH.+')
          if not match_str.search(cnfgfile):
            cnfgfile = generateConfile(request,fcid)
            if match_str.search(cnfgfile):
              rec = DataRun.objects.get(run_folder=runfolder) #,flowcell_id=fcid)
              rec.config_params = cnfgfile
              rec.save()
            else:
              cnfgfile = 'Failed generating config params for RunFolder = '+runfolder +', Flowcell id = '+ fcid+ ' Config Text:\n'+cnfgfile  
            
        except ObjectDoesNotExist:
          cnfgfile = 'Entry not found for RunFolder = '+runfolder

    return HttpResponse(cnfgfile, mimetype='text/plain')

def getLaneLibs(req):
    granted = False
    ClIP = req.META['REMOTE_ADDR']
    if (settings.ALLOWED_IPS.has_key(ClIP)):  granted = True

    if not granted: return HttpResponse("access denied.")

    request = req.REQUEST
    fcid = 'none'
    outputfile = ''
    if request.has_key('fcid'):
      fcid = request['fcid']
      try:                                
        rec = FlowCell.objects.get(flowcell_id=fcid)
        #Ex: 071211
        year = datetime.today().year.__str__()
        year = replace(year,'20','')
        month = datetime.today().month
        if month < 10: month = "0"+month.__str__()
        else: month = month.__str__() 
        day = datetime.today().day
        if day < 10: day = "0"+day.__str__()
        else: day = day.__str__()
        mydate = year+month+day
        outputfile = '<?xml version="1.0" ?>'
        outputfile += '\n<SolexaResult Date="'+mydate+'" Flowcell="'+fcid+'" Client="'+settings.ALLOWED_IPS[ClIP]+'">'
        outputfile += '\n<Lane Index="1" Name="'+rec.lane_1_library.library_name+'" Library="'+rec.lane_1_library.library_id+'" Genome="'+rec.lane_1_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="2" Name="'+rec.lane_2_library.library_name+'" Library="'+rec.lane_2_library.library_id+'" Genome="'+rec.lane_2_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="3" Name="'+rec.lane_3_library.library_name+'" Library="'+rec.lane_3_library.library_id+'" Genome="'+rec.lane_3_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="4" Name="'+rec.lane_4_library.library_name+'" Library="'+rec.lane_4_library.library_id+'" Genome="'+rec.lane_4_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="5" Name="'+rec.lane_5_library.library_name+'" Library="'+rec.lane_5_library.library_id+'" Genome="'+rec.lane_5_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="6" Name="'+rec.lane_6_library.library_name+'" Library="'+rec.lane_6_library.library_id+'" Genome="'+rec.lane_6_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="7" Name="'+rec.lane_7_library.library_name+'" Library="'+rec.lane_7_library.library_id+'" Genome="'+rec.lane_7_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n<Lane Index="8" Name="'+rec.lane_8_library.library_name+'" Library="'+rec.lane_8_library.library_id+'" Genome="'+rec.lane_8_library.library_species.use_genome_build+'" PrimerName="" PrimerSeq=""/>'
        outputfile += '\n</SolexaResult>'
      except ObjectDoesNotExist:
        outputfile = 'Flowcell entry not found for: '+fcid
    else: outputfile = 'Missing input: flowcell id'

    return HttpResponse(outputfile, mimetype='text/plain')

def estimateFlowcellDuration(flowcell):
    """
    Attempt to estimate how long it will take to run a flowcell

    """
    # (3600 seconds * 1.5 hours per cycle )
    sequencing_seconds_per_cycle= 3600 * 1.5
    # 800 is a rough guess
    pipeline_seconds_per_cycle = 800
    
    cycles = flowcell.read_length
    if flowcell.paired_end:
        cycles *= 2
    sequencing_time = timedelta(0, cycles * sequencing_seconds_per_cycle)
    analysis_time = timedelta(0, cycles * pipeline_seconds_per_cycle)
    estimate_mid = sequencing_time + analysis_time
    # floor estimate_mid
    estimate_low = timedelta(estimate_mid.days, 0)
    # floor estimate_mid and add a day
    estimate_high = timedelta(estimate_mid.days+1, 0)
    
    return (estimate_low, estimate_high)
    

def makeUserLaneMap(flowcell):
    """
    Given a flowcell return a mapping of users interested in
    the libraries on those lanes.
    """
    users = {}

    for lane in flowcell.lane_set.all():
        for affiliation in lane.library.affiliations.all():
            for user in affiliation.users.all():
                users.setdefault(user,[]).append(lane)

    return users

def makeUserLibrarMap(libraries):
    """
    Given an interable set of libraries return a mapping or
    users interested in those libraries.
    """
    users = {}
    
    for library in libraries:
        for affiliation in library.affiliations.all():
            for user in affiliation.users.all():
                users.setdefault(user,[]).append(library)
                
    return users
