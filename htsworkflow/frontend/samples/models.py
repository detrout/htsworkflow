from django.db import models
from django.contrib.auth.models import User
from htsworkflow.frontend import settings
from htsworkflow.frontend.reports.libinfopar import *

# Create your models here.

class Antibody(models.Model):
    antigene = models.CharField(max_length=500, db_index=True)
    # New field Aug/20/08
    # SQL to add column: 
    # alter table fctracker_antibody add column "nickname" varchar(20) NULL;
    nickname = models.CharField(
        max_length=20,
        blank=True,
        null=True, 
        db_index=True,
        verbose_name = 'Short Name'
    )
    catalog = models.CharField(max_length=50, unique=True, db_index=True)
    antibodies = models.CharField(max_length=500, db_index=True)
    source = models.CharField(max_length=500, blank=True, db_index=True)
    biology = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    def __unicode__(self):
        return u'%s - %s (%s)' % (self.antigene, self.antibodies, self.catalog)
    class Meta:
        verbose_name_plural = "antibodies"
        ordering = ["antigene"]

class Cellline(models.Model):
    cellline_name = models.CharField(max_length=100, unique=True, db_index=True)
    nickname = models.CharField(max_length=20,
        blank=True,
        null=True, 
        db_index=True,
        verbose_name = 'Short Name')
    notes = models.TextField(blank=True)
    def __unicode__(self):
        return unicode(self.cellline_name)

    class Meta:
        ordering = ["cellline_name"]

class Condition(models.Model):
    condition_name = models.CharField(
        max_length=2000, unique=True, db_index=True)
    nickname = models.CharField(max_length=20,
        blank=True,
        null=True, 
        db_index=True,
        verbose_name = 'Short Name')
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return unicode(self.condition_name)

    class Meta:
        ordering = ["condition_name"]

class Tag(models.Model): 
  tag_name = models.CharField(max_length=100, db_index=True,blank=False,null=False) 
  TAG_CONTEXT = ( 
      #('Antibody','Antibody'), 
      #('Cellline', 'Cellline'), 
      #('Condition', 'Condition'), 
      ('Library', 'Library'), 
      ('ANY','ANY'), 
  ) 
  context = models.CharField(max_length=50, 
      choices=TAG_CONTEXT, default='Library') 
 
  def __unicode__(self): 
    return u'%s' % (self.tag_name) 
 
  class Meta: 
    ordering = ["context","tag_name"] 
 
class Species(models.Model):
  scientific_name = models.CharField(max_length=256, 
      unique=False, 
      db_index=True
  )
  common_name = models.CharField(max_length=256, blank=True)
  #use_genome_build = models.CharField(max_length=100, blank=False, null=False)

  def __unicode__(self):
    return u'%s (%s)' % (self.scientific_name, self.common_name)
  
  class Meta:
    verbose_name_plural = "species"
    ordering = ["scientific_name"]
  
class Affiliation(models.Model):
  name = models.CharField(max_length=256, db_index=True, verbose_name='Group Name')
  contact = models.CharField(max_length=256, null=True, blank=True,verbose_name='Contact Name')  
  email = models.EmailField(null=True,blank=True)
  
  def __unicode__(self):
    str = unicode(self.name)
    if len(self.contact) != 0:
      str += u' ('+self.contact+u')' 
    return str

  class Meta:
    ordering = ["name","contact"]
    unique_together = (("name", "contact"),)

class Library(models.Model):
  
  library_id = models.CharField(max_length=30, primary_key=True, db_index=True)
  library_name = models.CharField(max_length=100, unique=True)
  library_species = models.ForeignKey(Species)
  cell_line = models.ForeignKey(Cellline)
  condition = models.ForeignKey(Condition)
  antibody = models.ForeignKey(Antibody,blank=True,null=True)
  # New field Aug/25/08. SQL: alter table fctracker_library add column "lib_affiliation" varchar(256)  NULL;
  affiliations = models.ManyToManyField(Affiliation,related_name='library_affiliations',null=True)
  # new field Nov/14/08
  tags = models.ManyToManyField(Tag,related_name='library_tags',blank=True,null=True)
  # New field Aug/19/08
  # SQL to add column: alter table fctracker_library add column "replicate" smallint unsigned NULL;
  REPLICATE_NUM = ((1,1),(2,2),(3,3),(4,4))
  replicate =  models.PositiveSmallIntegerField(choices=REPLICATE_NUM,default=1) 

  EXPERIMENT_TYPES = (
      ('INPUT_RXLCh','INPUT_RXLCh'),
      ('ChIP-seq', 'ChIP-seq'),
      ('Sheared', 'Sheared'),
      ('RNA-seq', 'RNA-seq'),
      ('Methyl-seq', 'Methyl-seq'),
      ('DIP-seq', 'DIP-seq'),
    ) 
  experiment_type = models.CharField(max_length=50, choices=EXPERIMENT_TYPES,
                                     default='RNA-seq')
  
  creation_date = models.DateField(blank=True, null=True)
  # made_for = models.ForeignKey(User)
  made_for = models.CharField(max_length=50, blank=True, 
      verbose_name='ChIP/DNA/RNA Made By')
  made_by = models.CharField(max_length=50, blank=True, default="Lorian")
  
  PROTOCOL_END_POINTS = (
      ('?', 'Unknown'),
      ('Sample', 'Raw sample'),
      ('Progress', 'In progress'),
      ('1A', 'Ligation, then gel'),
      ('PCR', 'Ligation, then PCR'),
      ('1Ab', 'Ligation, PCR, then gel'),
      ('1Aa', 'Ligation, gel, then PCR'),
      ('2A', 'Ligation, PCR, gel, PCR'),
      ('Done', 'Completed'),
    )
  stopping_point = models.CharField(max_length=25, choices=PROTOCOL_END_POINTS, default='Done')
  amplified_from_sample = models.ForeignKey('self', blank=True, null=True)  
  
  undiluted_concentration = models.DecimalField("Undiluted concentration (ng/ul)", max_digits=5, decimal_places=2, default=0, blank=True, null=True)
  successful_pM = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
  ten_nM_dilution = models.BooleanField()
  avg_lib_size = models.IntegerField(default=225, blank=True, null=True)
  notes = models.TextField(blank=True)
  
  def __unicode__(self):
    return u'#%s: %s' % (self.library_id, self.library_name)
  
  class Meta:
    verbose_name_plural = "libraries"
    ordering = ["-creation_date"] #["-library_id"]
  
  def antibody_name(self):
    str ='<a target=_self href="/admin/samples/antibody/'+self.antibody.id.__str__()+'/" title="'+self.antibody.__str__()+'">'+self.antibody.nickname+'</a>' 
    return str
  antibody_name.allow_tags = True

  def organism(self):
    return self.library_species.common_name

  def affiliation(self):
    affs = self.affiliations.all().order_by('name')
    tstr = ''
    ar = []
    for t in affs:
        ar.append(t.__unicode__())
    return '%s' % (", ".join(ar))

  def libtags(self):
    affs = self.tags.all().order_by('tag_name')
    ar = []
    for t in affs:
      ar.append(t.__unicode__())
    return u'%s' % ( ", ".join(ar))

  def DataRun(self):
    str ='<a target=_self href="/admin/experiments/datarun/?q='+self.library_id+'" title="Check All Data Runs for This Specific Library ..." ">Data Run</a>' 
    return str
  DataRun.allow_tags = True

  def aligned_m_reads(self):
    return getLibReads(self.library_id)

  def aligned_reads(self):
    res = getLibReads(self.library_id)

    # Check data sanity
    if res[2] != "OK":
      return u'<div style="border:solid red 2px">'+res[2]+'</div>'

    rc = "%1.2f" % (res[1]/1000000.0)
    # Color Scheme: green is more than 10M, blue is more than 5M, orange is more than 3M and red is less. For RNAseq, all those thresholds should be doubled
    if res[0] > 0:
      bgcolor = '#ff3300'  # Red
      rc_thr = [10000000,5000000,3000000]
      if self.experiment_type == 'RNA-seq':
        rc_thr = [20000000,10000000,6000000]

      if res[1] > rc_thr[0]:
        bgcolor = '#66ff66'  # Green
      else:
        if res[1] > rc_thr[1]:
          bgcolor ='#00ccff'  # Blue
        else:
           if res[1] > rc_thr[2]: 
             bgcolor ='#ffcc33'  # Orange
      tstr = '<div style="background-color:'+bgcolor+';color:black">'
      tstr += res[0].__unicode__()+' Lanes, '+rc+' M Reads'
      tstr += '</div>'
    else: tstr = 'not processed yet' 
    return tstr
  aligned_reads.allow_tags = True

