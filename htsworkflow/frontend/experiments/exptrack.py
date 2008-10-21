# some core functions of the exp tracker module
from django.http import HttpResponse
from datetime import datetime
from string import *
import re
from htswfrontend import settings
from htswfrontend.exp_track.models import FlowCell, DataRun
from htswfrontend.fctracker.models import Library
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
    granted = False    

    if request.has_key('user'):
      user = request['user']

    #Check access permission 
    if (user == 'rami' and settings.ALLOWED_IPS.has_key(ClIP)):  granted = True
    if not granted: return HttpResponse("access denied.")


    # ~~~~~~Parameters for the job ~~~~
    if request.has_key('fcid'):
      fcid = request['fcid']
    else:
      return HttpResponse('missing fcid')
    
    if request.has_key('runf'):
      runfolder = request['runf']
    else:
      return HttpResponse('missing runf')

    
    if request.has_key('updst'):
      UpdatedStatus = request['updst']
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
      if request.has_key('msg'):
        rec.run_note += ", "+request['msg']+" ("+mytimestamp+")"
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

    cnfgfile = 'READ_LENGTH 25\n'
    cnfgfile += 'ANALYSIS eland\n'
    cnfgfile += 'GENOME_FILE all_chr.fa\n'
    cnfgfile += 'ELAND_MULTIPLE_INSTANCES 8\n'
    genome_dir = 'GENOME_DIR /Volumes/Genomes/'
    eland_genome = 'ELAND_GENOME /Volumes/Genomes/'
    
    try:                                                                                                                                              
      rec = FlowCell.objects.get(flowcell_id=fcid)
      
      cnfgfile += '1:'+genome_dir+rec.lane_1_library.library_species.use_genome_build+'\n'
      cnfgfile += '1:'+eland_genome+rec.lane_1_library.library_species.use_genome_build+'\n'

      cnfgfile += '2:'+genome_dir+rec.lane_2_library.library_species.use_genome_build+'\n'
      cnfgfile += '2:'+eland_genome+rec.lane_2_library.library_species.use_genome_build+'\n'
 
      cnfgfile += '3:'+genome_dir+rec.lane_3_library.library_species.use_genome_build+'\n'
      cnfgfile += '3:'+eland_genome+rec.lane_3_library.library_species.use_genome_build+'\n'

      cnfgfile += '4:'+genome_dir+rec.lane_4_library.library_species.use_genome_build+'\n'
      cnfgfile += '4:'+eland_genome+rec.lane_4_library.library_species.use_genome_build+'\n'
      
      cnfgfile += '5:'+genome_dir+rec.lane_5_library.library_species.use_genome_build+'\n'
      cnfgfile += '5:'+eland_genome+rec.lane_5_library.library_species.use_genome_build+'\n'

      cnfgfile += '6:'+genome_dir+rec.lane_6_library.library_species.use_genome_build+'\n'
      cnfgfile += '6:'+eland_genome+rec.lane_6_library.library_species.use_genome_build+'\n'

      cnfgfile += '7:'+genome_dir+rec.lane_7_library.library_species.use_genome_build+'\n'
      cnfgfile += '7:'+eland_genome+rec.lane_7_library.library_species.use_genome_build+'\n'

      cnfgfile += '8:'+genome_dir+rec.lane_8_library.library_species.use_genome_build+'\n'
      cnfgfile += '8:'+eland_genome+rec.lane_8_library.library_species.use_genome_build

    except ObjectDoesNotExist:
      cnfgfile = 'Entry not found for fcid  = '+fcid

    return cnfgfile

def getConfile(request):
    granted = False
    ClIP = request.META['REMOTE_ADDR']
    if (settings.ALLOWED_IPS.has_key(ClIP)):  granted = True

    if not granted: return HttpResponse("access denied. IP: "+ClIP)

    fcid = 'none'
    cnfgfile = ''
    runfolder = 'unknown'
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

    return HttpResponse(cnfgfile)

def getLaneLibs(request):
    granted = False
    ClIP = request.META['REMOTE_ADDR']
    if (settings.ALLOWED_IPS.has_key(ClIP)):  granted = True

    if not granted: return HttpResponse("access denied.")

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

    return HttpResponse(outputfile)
