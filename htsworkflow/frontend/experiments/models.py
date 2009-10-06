import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core import urlresolvers
from django.db import models

from htsworkflow.frontend.samples.models import *
from htsworkflow.frontend.settings import options

class ClusterStation(models.Model):
  name = models.CharField(max_length=50, unique=True)

  def __unicode__(self):
    return unicode(self.name)

class Sequencer(models.Model):
  name = models.CharField(max_length=50, unique=True)

  def __unicode__(self):
    return unicode(self.name)

default_pM = 5
try:
  default_pM = int(options.get('frontend', 'default_pm'))
except ValueError,e:
  logging.error("invalid value for frontend.default_pm")

class FlowCell(models.Model):
  
  flowcell_id = models.CharField(max_length=20, unique=True, db_index=True)
  run_date = models.DateTimeField()
  advanced_run = models.BooleanField(default=False)
  paired_end = models.BooleanField(default=False)
  read_length = models.IntegerField(default=32) #Stanford is currenlty 25
  control_lane = models.IntegerField(choices=[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)], null=True)

  cluster_station = models.ForeignKey(ClusterStation, default=3)
  sequencer = models.ForeignKey(Sequencer, default=1)
  
  notes = models.TextField(blank=True)

  def __unicode__(self):
      return unicode(self.flowcell_id) 

  def Create_LOG(self):
    str = ''
    str +='<a target=_balnk href="/experiments/'+self.flowcell_id+'" title="Create XLS like sheet for this Flowcell ..." ">Create LOG</a>'
    try:
      t = DataRun.objects.get(fcid=self.id)
      str +='<br/><a target=_self href="/admin/experiments/datarun/?q='+self.flowcell_id+'" title="Check Data Runs ..." ">DataRun ..</a>'
    except ObjectDoesNotExist:
      str += '<br/><span style="color:red">not sequenced</span>'
    return str
  Create_LOG.allow_tags = True 

  def Lanes(self):
    library_url = '/admin/samples/library/%s' 
    html = ['<table>']
    #for i in range(1,9):
    for lane in self.lane_set.all():
        cluster_estimate = lane.cluster_estimate
        if cluster_estimate is not None:
            cluster_estimate = "%s k" % ((int(cluster_estimate)/1000), )
        else:
            cluster_estimate = 'None'
        library_id = lane.library_id
        library = lane.library
        element = '<tr><td>%d</td><td><a href="%s">%s</a></td><td>%s</td></tr>'
        expanded_library_url = library_url %(library_id,)
        html.append(element % (lane.lane_number, expanded_library_url, library, cluster_estimate))
    html.append('</table>')
    return "\n".join(html)
  Lanes.allow_tags = True

  class Meta:
    ordering = ["-run_date"]

  def get_admin_url(self):
    # that's the django way... except it didn't work
    #return urlresolvers.reverse('admin_experiments_FlowCell_change', args=(self.id,))
    return '/admin/experiments/flowcell/%s/' % (self.id,)
  
### -----------------------
class DataRun(models.Model):
  ConfTemplate = "CONFIG PARAMS WILL BE GENERATED BY THE PIPELINE SCRIPT.\nYOU'LL BE ABLE TO EDIT AFTER IF NEEDED."
  run_folder = models.CharField(max_length=50,unique=True, db_index=True)
  fcid = models.ForeignKey(FlowCell,verbose_name="Flowcell Id")
  config_params = models.TextField(default=ConfTemplate)
  run_start_time = models.DateTimeField()
  RUN_STATUS_CHOICES = (
      (0, 'Sequencer running'), ##Solexa Data Pipeline Not Yet Started'),
      (1, 'Data Pipeline Started'),
      (2, 'Data Pipeline Interrupted'),
      (3, 'Data Pipeline Finished'),
      (4, 'CollectReads Started'),
      (5, 'CollectReads Finished'),
      (6, 'QC Finished'),
      (7, 'DONE'),
    )
  run_status = models.IntegerField(choices=RUN_STATUS_CHOICES, default=0)
  run_note = models.TextField(blank=True)


  def main_status(self):
    str = '<div'
    if self.run_status >= 5:
      str += ' style="color:green">'
      str += '<b>'+self.RUN_STATUS_CHOICES[self.run_status][1]+'</b>'
      str += '<br/><br/>' #<span style="color:red;font-size:80%;">New!</span>'
      str +='<br/><a target=_balnk href="'+settings.TASKS_PROJS_SERVER+'/Flowcells/'+self.fcid.flowcell_id+'/'+self.fcid.flowcell_id+'_QC_Summary.html" title="View QC Summaries of this run ..." ">View QC Page</a>'
    else:
      str += '>'+self.RUN_STATUS_CHOICES[self.run_status][1]

    str += '</div>'
    return str
  main_status.allow_tags = True

  main_status.allow_tags = True
  
  def Flowcell_Info(self):
    str = '<b>'+self.fcid.__str__()+'</b>'
    str += '  (c: '+self.fcid.cluster_mac_id+',  s: '+self.fcid.seq_mac_id+')'
    str += '<div style="margin-top:5px;">'    
    str +='<a title="View Lane List here ..."  onClick="el = document.getElementById(\'LanesOf'+self.fcid.__str__()+'\');if(el) (el.style.display==\'none\'?el.style.display=\'block\':el.style.display=\'none\')" style="cursor:pointer;color: #5b80b2;">View/hide lanes</a>'
    str += '<div id="LanesOf'+self.fcid.__str__()+'" style="display:block;border:solid #cccccc 1px;width:350px">'
    LanesList = '1: '+self.fcid.lane_1_library.__str__()+' ('+self.fcid.lane_1_library.library_species.use_genome_build+')<br/>2: '+self.fcid.lane_2_library.__str__()+' ('+self.fcid.lane_2_library.library_species.use_genome_build+')<br/>3: '+self.fcid.lane_3_library.__str__()+' ('+self.fcid.lane_3_library.library_species.use_genome_build+')<br/>4: '+self.fcid.lane_4_library.__str__()+' ('+self.fcid.lane_4_library.library_species.use_genome_build+')<br/>5: '+self.fcid.lane_5_library.__str__()+' ('+self.fcid.lane_5_library.library_species.use_genome_build+')<br/>6: '+self.fcid.lane_6_library.__str__()+' ('+self.fcid.lane_6_library.library_species.use_genome_build+')<br/>7: '+self.fcid.lane_7_library.__str__()+' ('+self.fcid.lane_7_library.library_species.use_genome_build+')<br/>8: '+self.fcid.lane_8_library.__str__()+' ('+self.fcid.lane_8_library.library_species.use_genome_build+')'
    str += LanesList ## self.fcid.Lanes()
    str += '</div>'
    str += '<div><a title="open Flowcell record" href="/admin/exp_track/flowcell/'+self.fcid.id.__str__()+'/" target=_self>Edit Flowcell record</a>'
    #str += '<span style="color:red;font-size:80%;margin-left:15px;margin-right:3px">New!</span>'
    str +='<a style="margin-left:15px;" target=_balnk href="/exp_track/'+self.fcid.flowcell_id+'" title="View XLS like sheet for this Flowcell LOG ..." ">GA LOG Page</a>'
    str += '</div>'
    str += '</div>'    
    return str
  Flowcell_Info.allow_tags = True


class Lane(models.Model):
  flowcell = models.ForeignKey(FlowCell)
  lane_number = models.IntegerField(choices=[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)])
  library = models.ForeignKey(Library)
  pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  cluster_estimate = models.IntegerField(blank=True, null=True)
  comment = models.TextField(null=True, blank=True)
