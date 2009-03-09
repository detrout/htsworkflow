from django.db import models
from htsworkflow.frontend.samples.models import *
from htsworkflow.frontend.settings import options
from django.core.exceptions import ObjectDoesNotExist
import logging

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
  
  lane_1_library = models.ForeignKey(Library, related_name="lane_1_library")
  lane_2_library = models.ForeignKey(Library, related_name="lane_2_library")
  lane_3_library = models.ForeignKey(Library, related_name="lane_3_library")
  lane_4_library = models.ForeignKey(Library, related_name="lane_4_library")
  lane_5_library = models.ForeignKey(Library, related_name="lane_5_library")
  lane_6_library = models.ForeignKey(Library, related_name="lane_6_library")
  lane_7_library = models.ForeignKey(Library, related_name="lane_7_library")
  lane_8_library = models.ForeignKey(Library, related_name="lane_8_library")

  lane_1_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_2_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_3_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_4_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_5_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_6_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_7_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  lane_8_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=default_pM)
  
  lane_1_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_2_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_3_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_4_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_5_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_6_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_7_cluster_estimate = models.IntegerField(blank=True, null=True)
  lane_8_cluster_estimate = models.IntegerField(blank=True, null=True)
 
  # lane_1_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_1_primer")
  # lane_2_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_2_primer")
  # lane_3_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_3_primer")
  # lane_4_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_4_primer")
  # lane_5_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_5_primer")
  # lane_6_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_6_primer")
  # lane_7_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_7_primer")
  # lane_8_primer = models.ForeignKey(Primer,blank=True,null=True,related_name="lane_8_primer")

  #cluster_mac_id = models.CharField(max_length=50, choices=CLUSTER_MAC, default='BitBit')
  #seq_mac_id = models.CharField(max_length=50, choices=SEQ_MAC, verbose_name = 'Sequencer', default='Britney')
  cluster_station = models.ForeignKey(ClusterStation)
  sequencer = models.ForeignKey(Sequencer)
  
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
    for i in range(1,9):
        cluster_estimate = getattr(self, 'lane_%d_cluster_estimate' % (i,))
        if cluster_estimate is not None:
            cluster_estimate = "%s k" % ((int(cluster_estimate)/1000), )
        else:
            cluster_estimate = 'None'
	library_id = getattr(self, 'lane_%d_library_id' % (i,))
        library = getattr(self, 'lane_%d_library' % i)
	element = '<tr><td>%d</td><td><a href="%s">%s</a></td><td>%s</td></tr>'
        expanded_library_url = library_url %(library_id,)
        html.append(element % (i, expanded_library_url, library, cluster_estimate))
    html.append('</table>')
    return "\n".join(html)
  Lanes.allow_tags = True

  class Meta:
    ordering = ["-run_date"]
  
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
