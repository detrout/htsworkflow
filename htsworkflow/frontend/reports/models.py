from django.db import models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from htsworkflow.frontend.samples.models import * 
from htsworkflow.frontend.analysis.models import *
from htsworkflow.frontend.experiments.models import *
from string import *
from htsworkflow.frontend.reports.utils import *
import re
##from p1 import LibInfo
from libinfopar import *

## This is a table based REPORT generator. The goal is to display a Progress Report for all the ENCODE projects, based on Study Name (e.g. NRSF, FOXP2, Methy-Seq on .. etc).
  
class ProgressReport(models.Model):
  st_sbj = models.ForeignKey(Project,limit_choices_to = Q(project_name__startswith='ENCODE '),related_name='project',db_index=True,verbose_name="Studied Subject")
  interactome_complete = models.BooleanField(default=False)

  def Study(self):
    str = self.st_sbj.__str__()
    str += '<br/><br/>'
    str += '<a title="open Project record" href="/admin/analys_track/project/'+self.st_sbj.id.__str__()+'/" target=_self style="font-size:85%">Edit Project</a>'
    return str  
  Study.allow_tags = True

  def submit_to_DCC(self):
    varText = ''
    if self.note_about_DCC:
      varText += '<br/><u>Note:</u><br/>'+self.note_about_DCC
    return '%s<br/>%s' % (self.submitted_to_DCC,varText)
  submit_to_DCC.allow_tags = True

  def submit_to_NCBI(self):
    varText = ''
    if self.note_about_NCBI:
      varText += '<br/><u>Note:</u><br/>'+self.note_about_NCBI 
    return '%s<br/>%s' % (self.submitted_to_NCBI,varText)
  submit_to_NCBI.allow_tags = True

  ## -- Utility functions <-- This method was transfered to untils.py

  ## --- LIBARAY PREPARATION SECTION 
  def getLibIds(self):
    ptasks = self.st_sbj.tasks.distinct()
    arLibs = [] 
    for t in ptasks:
      if t.subject1 is not None:
        arLibs.append(t.subject1.library_id)
      if t.subject2 is not None:
        arLibs.append(t.subject2.library_id)
    arLibs = unique(arLibs)
    return arLibs #.sort()

  def getFCInfo(self,libid):   ## This is the haviest function 
    arFCLanes = []
    ##Test return arFCLanes
    # can't get this to work: FC_L1 = FlowCell.objects.filter(lane_5_library__exact=libid)
    allFCs = FlowCell.objects.all()
    for f in allFCs:
      entry = ''
      lanes = []
      #found = False
#      for i in range(1,9):
#        if eval('f.lane_'+i.__str__()+'_library.library_id==libid'):
#          lanes.append(i.__str__())
#          found = True

# maybe a bit faster this way:
      if f.lane_1_library.library_id==libid:
          lanes.append('1')
          #found = True
      if f.lane_2_library.library_id==libid:
          lanes.append('2')
          #found = True
      if f.lane_3_library.library_id==libid:
          lanes.append('3')
          #found = True
      if f.lane_4_library.library_id==libid:
          lanes.append('4')
          #found = True
      if f.lane_5_library.library_id==libid:
          lanes.append('5')
          #found = True
      if f.lane_6_library.library_id==libid:
          lanes.append('6')
          #found = True
      if f.lane_7_library.library_id==libid:
          lanes.append('7')
          #found = True
      if f.lane_8_library.library_id==libid:
          lanes.append('8')
          #found = True


      #if found:
      if len(lanes)>0:
        rundate = re.sub(pattern="\s.*$",repl="",string=f.run_date.__str__())
        entry = '<b>'+f.flowcell_id + '</b> Lanes No.: '+','.join(lanes)+' ('+rundate+')' 
        arFCLanes.append(entry)    
    if len(arFCLanes)==0:
      arFCLanes.append('<font color=red>Flowcell not found.</font>')
    return arFCLanes

  def ab_batch(self):
    ##  To have the Company's lot number, apearing on the (source) tube, we need to add new Field in Library. 
    arlibs = self.getLibIds()
    tstr = '<ul>' ##<u><b>Ab</b> from '+len(arlibs).__str__()+' libs</u>: '
    arRows = []
    for l in arlibs:
      try:
        rec = Library.objects.get(library_id=l,antibody__isnull=False)
        arRows.append('<li>'+rec.antibody.antibodies+' for <b>'+rec.antibody.antigene+'</b> (src:'+rec.antibody.source+', cat:'+rec.antibody.catalog+')</li>')
      except ObjectDoesNotExist:
        tstr += ""
    tstr += "".join(unique(arRows))+'</ul>'
    return tstr
  ab_batch.allow_tags = True

  def cell_line(self):                                                                                           
    arlibs = self.getLibIds()
    tstr = '<ul>'
    arRows = []                                                                                                                                     
    for l in arlibs:
      try:
        rec = Library.objects.get(library_id=l)
        arRows.append('<li><b>'+rec.cell_line.cellline_name+'</b> ('+rec.condition.condition_name+')</li>')
      except ObjectDoesNotExist:
        tstr += ""                                                                                                                               
    tstr += "".join(unique(arRows))+'</ul>'
    return tstr
  cell_line.allow_tags = True

  def cell_harvest_batch(self): # <- data now displayed in "cell_line"
    ## name + date  
    arlibs = self.getLibIds()
    tstr = '<ul>'
    arRows = []
    for l in arlibs:
      try:
        rec = Library.objects.get(library_id=l)
        arRows.append('<li><b>'+rec.condition.condition_name+'</b></li>')
      except ObjectDoesNotExist:
        tstr += ""
    tstr += "".join(unique(arRows))+'</ul>'
    return tstr
  cell_harvest_batch.allow_tags = True

  def ChIP_made(self):
    ## person + date                                                                                                                                                                                                             
    return '...'

  def library(self):
    ## Lib Id + Date + Person
    tstr = '<script>'
    tstr += 'function togit(eid){'
    tstr += 'f=document.getElementById(eid);'
    tstr += 'if(f.style.display==\'none\'){'
    tstr += 'f.style.display=\'block\';'
    tstr += '}else{'
    tstr += 'f.style.display=\'none\';'
    tstr += '}'
    tstr += '}'
    tstr += '</script>'
    arlibs = self.getLibIds() ##.sort()
    arlibs = arlibs
    tstr +='<a href=# onClick="togit(\'libInfo'+self.st_sbj.project_name+'\')">view /hide</a>'
    tstr += '<div id="libInfo'+self.st_sbj.project_name+'" style="display:block;border:solid #cccccc 1px;width:200px;height:300px;overflow:auto"><ul>'
    arRows = []
    for l in arlibs:
      try:
        rec = Library.objects.get(library_id=l)
        arRows.append('<li><b>'+rec.library_id+'</b>: '+rec.library_name+'.<br/>Made By: '+rec.made_by+', On: '+ rec.creation_date.__str__()+'</li>')
      except ObjectDoesNotExist:
        tstr += ""
    tstr += "".join(unique(arRows))+'</ul></div>'
    return tstr
  library.allow_tags = True


  ## -- SEQUENCING SECTION 
  def sequencing(self):
    ## FCId + Lane + Date
    arlibs = self.getLibIds()
    tstr ='<a href=# onClick="togit(\'seqInfo'+self.st_sbj.project_name+'\')">view /hide</a>'
    tstr += '<div id="seqInfo'+self.st_sbj.project_name+'" style="display:block;border:solid #cccccc 1px;width:200px;height:300px;overflow:auto"><ul>'    
    for l in arlibs:
      tstr += '<li><b>'+l+'</b>:<br/>'+(' / '.join(self.getFCInfo(l)))+'</li>'
    tstr += '</ul></div>'
    return tstr
  sequencing.allow_tags = True
  
  def aligned_reads(self):
    ## Mega reads/lane                                              
    arlibs = self.getLibIds()
    tstr = '<a href=# onClick="togit(\'readsInfo'+self.st_sbj.project_name+'\')">view /hide</a>'
    tstr += '<div id="readsInfo'+self.st_sbj.project_name+'" style="display:block;border:solid #cccccc 1px;width:200px;height:300px;overflow:auto">'
    tstr += '<table><tr><td>Library Id</td><td>Total Lanes</td><td>M Reads</td></tr>'
    LanesCnt, ReadsCnt = 0, 0
    for l in arlibs:      
      res = getLibReads(l)
      LanesCnt += res[0]
      ReadsCnt += res[1]
      rc = "%1.2f" % (res[1]/1000000.0)
      tstr += '<tr><td><b>'+l+'</b></td><td>'+res[0].__str__()+'</td></td><td>'+rc+'</td></tr>'
    tstr += '</table>'
    #tstr += '<a target=_blank href="http://m304-apple-server.stanford.edu/projects/'+self.st_sbj.id.__str__()+'">Project results page</a>'
    tstr += '</div>'
    myNum = (ReadsCnt/1000000.0)
    myNum  = "%1.2f" % (myNum) 
    tstr += '<div>Total: <b>'+LanesCnt.__str__()+'</b> lanes and <b>'+myNum+'</b> M Reads</div>'
    tstr += '<a target=_blank href="http://m304-apple-server.stanford.edu/projects/'+self.st_sbj.id.__str__()+'">Project results page</a>'
    return tstr
  aligned_reads.allow_tags = True

  def peak_calling(self):
    # date + what etc..
    return 'coming up ..'

  QPCR = models.CharField(max_length=500,blank=True,null=True)    
  submitted_to_DCC = models.DateTimeField(blank=True,null=True)
  submitted_to_NCBI = models.DateTimeField(blank=True,null=True)
  note_about_DCC =  models.TextField(blank=True)
  note_about_NCBI = models.TextField(blank=True)
  
  def __str__(self):
      return '"%s" - %s' % (self.st_sbj,self.interactome_complete)

  class Meta:
    #verbose_name_plural = "Reports"
    ordering = ["id"]

  class Admin:
    list_display = ('Study','ab_batch','cell_line','library','sequencing','aligned_reads','QPCR','submit_to_DCC','submit_to_NCBI','interactome_complete')
    ## list_filter = ('interactome_complete')
    

#############################################
