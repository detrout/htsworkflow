from django.db import models
from htswfrontend.fctracker.models import *

class FlowCell(models.Model):
  
  flowcell_id = models.CharField(max_length=20, unique=True, db_index=True, core=True)
  run_date = models.DateTimeField(core=True)
  advanced_run = models.BooleanField(default=False)
  read_length = models.IntegerField(default=32) #Stanford is currenlty 25
  
  lane_1_library = models.ForeignKey(Library, related_name="lane_1_library")
  lane_2_library = models.ForeignKey(Library, related_name="lane_2_library")
  lane_3_library = models.ForeignKey(Library, related_name="lane_3_library")
  lane_4_library = models.ForeignKey(Library, related_name="lane_4_library")
  lane_5_library = models.ForeignKey(Library, related_name="lane_5_library")
  lane_6_library = models.ForeignKey(Library, related_name="lane_6_library")
  lane_7_library = models.ForeignKey(Library, related_name="lane_7_library")
  lane_8_library = models.ForeignKey(Library, related_name="lane_8_library")

  lane_1_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_2_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_3_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_4_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_5_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_6_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_7_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  lane_8_pM = models.DecimalField(max_digits=5, decimal_places=2,blank=False, null=False,default=2.5)
  
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

  #Machine Names
  CLUSTER_MAC = (
      ('M304','Cardinal'),
      ('R349','R349'),
      ('Tinkerbell','Tinkerbell'),
      ('BitBit','BitBit'),
    )
  
  SEQ_MAC = (
      ('EAS149','Stanford'),
      ('EAS46','EAS46'),
      ('EAS45','Paris'),
      ('Britney','Britney'),
    )
  
  cluster_mac_id = models.CharField(max_length=50, choices=CLUSTER_MAC, default='BitBit')
  seq_mac_id = models.CharField(max_length=50, choices=SEQ_MAC, verbose_name = 'Sequencer', default='Britney')
  
  notes = models.TextField(blank=True)

  def __str__(self):
    #return '%s (%s)' % (self.flowcell_id, self.run_date) 
    return '%s' % (self.flowcell_id) 

  def Create_LOG(self):
    str = '' #<span style="color:red;font-size:80%;margin-right:3px">New!</span>'
    str +='<a target=_balnk href="/exp_track/'+self.flowcell_id+'" title="Create XLS like sheet for this Flowcell ..." ">Create LOG</a>'
    return str
  Create_LOG.allow_tags = True 

  def Lanes(self):
    return '<div><span style="margin-right:10px">1)%s</span><span style="margin-right:10px">2)%s</span><span style="margin-right:10px">3)%s</span><span style="margin-right:10px">4)%s</span><span style="margin-right:10px">5)%s</span><span style="margin-right:10px">6)%s</span><span style="margin-right:10px">7)%s</span><span style="margin-right:10px">8)%s</span></div>' % (self.lane_1_library,self.lane_2_library,self.lane_3_library,self.lane_4_library,self.lane_5_library,self.lane_6_library,self.lane_7_library,self.lane_8_library)
  Lanes.allow_tags = True
 
  class Meta:
    ordering = ["-run_date"]
  
  class Admin:
    save_on_top = True
    date_hierarchy = "run_date"
    save_on_top = True
    search_fields = ['flowcell_id','seq_mac_id','cluster_mac_id','=lane_1_library__library_id','=lane_2_library__library_id','=lane_3_library__library_id','=lane_4_library__library_id','=lane_5_library__library_id','=lane_6_library__library_id','=lane_7_library__library_id','=lane_8_library__library_id']
    list_display = ('flowcell_id','seq_mac_id','run_date', 'Create_LOG','Lanes')
    list_filter = ('seq_mac_id','cluster_mac_id')
    fields = (
        (None, {
            'fields': ('run_date', ('flowcell_id','cluster_mac_id','seq_mac_id'), ('read_length'),)
        }),
        ('Lanes:', {
            ##'fields' : (('lane_1_library', 'lane_1_pM', 'lane_1_cluster_estimate', 'lane_1_primer'), ('lane_2_library', 'lane_2_pM', 'lane_2_cluster_estimate', 'lane_2_primer'), ('lane_3_library', 'lane_3_pM', 'lane_3_cluster_estimate', 'lane_3_primer'), ('lane_4_library', 'lane_4_pM', 'lane_4_cluster_estimate', 'lane_4_primer'), ('lane_5_library', 'lane_5_pM', 'lane_5_cluster_estimate', 'lane_5_primer'), ('lane_6_library', 'lane_6_pM', 'lane_6_cluster_estimate', 'lane_6_primer'), ('lane_7_library', 'lane_7_pM', 'lane_7_cluster_estimate', 'lane_7_primer'), ('lane_8_library', 'lane_8_pM', 'lane_8_cluster_estimate', 'lane_8_primer'),)
           'fields' : (('lane_1_library', 'lane_1_pM', 'lane_1_cluster_estimate'), ('lane_2_library', 'lane_2_pM', 'lane_2_cluster_estimate'), ('lane_3_library', 'lane_3_pM', 'lane_3_cluster_estimate'), ('lane_4_library', 'lane_4_pM', 'lane_4_cluster_estimate'), ('lane_5_library', 'lane_5_pM', 'lane_5_cluster_estimate'), ('lane_6_library', 'lane_6_pM', 'lane_6_cluster_estimate'), ('lane_7_library', 'lane_7_pM', 'lane_7_cluster_estimate'), ('lane_8_library', 'lane_8_pM', 'lane_8_cluster_estimate'),)
        }),
	(None, {
	    'fields' : ('notes',)
	}),
    )


### -----------------------
class DataRun(models.Model):
  ConfTemplate = "CONFIG PARAMS WILL BE GENERATED BY THE PIPELINE SCRIPT.\nYOU'LL BE ABLE TO EDIT AFTER IF NEEDED."
  run_folder = models.CharField(max_length=50,unique=True, db_index=True)
  fcid = models.ForeignKey(FlowCell,verbose_name="Flowcell Id")
  config_params = models.TextField(default=ConfTemplate)
  run_start_time = models.DateTimeField(core=True)
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
      str +='<br/><a target=_balnk href="http://m304-apple-server.stanford.edu/'+self.fcid.flowcell_id+'_QC/'+self.fcid.flowcell_id+'_'+self.run_folder+'_QC_Summary.html" title="View QC Summaries of this run ..." ">View QC Page</a>'
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

  class Admin:
    search_fields = ['run_folder','run_note','config_params','=fcid__lane_1_library__library_id','=fcid__lane_2_library__library_id','=fcid__lane_3_library__library_id','=fcid__lane_4_library__library_id','=fcid__lane_5_library__library_id','=fcid__lane_6_library__library_id','=fcid__lane_7_library__library_id','=fcid__lane_8_library__library_id']

    list_display = ('run_folder','Flowcell_Info','run_start_time','main_status','run_note')
    list_filter = ('run_status','run_start_time')
