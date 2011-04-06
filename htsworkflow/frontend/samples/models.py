import logging
import urlparse
from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models.signals import pre_save, post_save
from django.db import connection
from htsworkflow.frontend.reports.libinfopar import *


# Create your models here.
logger = logging.getLogger(__name__)

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

class ExperimentType(models.Model):
  name = models.CharField(max_length=50, unique=True)

  def __unicode__(self):
    return unicode(self.name)

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

  @models.permalink
  def get_absolute_url(self):
    return ('htsworkflow.frontend.samples.views.species', [str(self.id)])
  
class Affiliation(models.Model):
  name = models.CharField(max_length=256, db_index=True, verbose_name='Name')
  contact = models.CharField(max_length=256, null=True, blank=True,verbose_name='Lab Name')  
  email = models.EmailField(null=True,blank=True)
  users = models.ManyToManyField('HTSUser', null=True, blank=True)
  users.admin_order_field = "username"
  
  def __unicode__(self):
    str = unicode(self.name)
    if self.contact is not None and len(self.contact) > 0:
      str += u' ('+self.contact+u')' 
    return str

  def Users(self):
      users = self.users.all().order_by('username')
      return ", ".join([unicode(a) for a in users ])

  class Meta:
    ordering = ["name","contact"]
    unique_together = (("name", "contact"),)

class LibraryType(models.Model):
  name = models.CharField(max_length=255, unique=True)

  def __unicode__(self):
    return unicode(self.name)


class Library(models.Model):
  id = models.CharField(max_length=10, primary_key=True)
  library_name = models.CharField(max_length=100, unique=True)
  library_species = models.ForeignKey(Species)
  # new field 2008 Mar 5, alter table samples_library add column "hidden" NOT NULL default 0;
  hidden = models.BooleanField()
  # new field 2009 Oct 6, alter table samples_library add column "account_number" varchar(100) NULL
  account_number = models.CharField(max_length=100, null=True, blank=True)
  cell_line = models.ForeignKey(Cellline, blank=True, null=True, verbose_name="Background")
  condition = models.ForeignKey(Condition, blank=True, null=True)
  antibody = models.ForeignKey(Antibody,blank=True,null=True)
  # New field Aug/25/08. SQL: alter table fctracker_library add column "lib_affiliation" varchar(256)  NULL;
  affiliations = models.ManyToManyField(Affiliation,related_name='library_affiliations',null=True)
  # new field Nov/14/08
  tags = models.ManyToManyField(Tag,related_name='library_tags',blank=True,null=True)
  # New field Aug/19/08
  # SQL to add column: alter table fctracker_library add column "replicate" smallint unsigned NULL;
  REPLICATE_NUM = ((1,1),(2,2),(3,3),(4,4))
  replicate =  models.PositiveSmallIntegerField(choices=REPLICATE_NUM,default=1) 
  experiment_type = models.ForeignKey(ExperimentType)
  library_type = models.ForeignKey(LibraryType, blank=True, null=True)
  creation_date = models.DateField(blank=True, null=True)
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
      ('1Ac', 'Ligation, gel, then 12x PCR'),
      ('1Aa', 'Ligation, gel, then 18x PCR'),
      ('2A', 'Ligation, PCR, gel, PCR'),
      ('Done', 'Completed'),
    )
  PROTOCOL_END_POINTS_DICT = dict(PROTOCOL_END_POINTS)
  
  stopping_point = models.CharField(max_length=25, choices=PROTOCOL_END_POINTS, default='Done')
  amplified_from_sample = models.ForeignKey('self', blank=True, null=True, related_name='amplified_into_sample')  
  
  undiluted_concentration = models.DecimalField("Concentration", 
      max_digits=5, decimal_places=2, blank=True, null=True,
      help_text=u"Undiluted concentration (ng/\u00b5l)") 
      # note \u00b5 is the micro symbol in unicode
  successful_pM = models.DecimalField(max_digits=9, decimal_places=1, blank=True, null=True)
  ten_nM_dilution = models.BooleanField()
  gel_cut_size = models.IntegerField(default=225, blank=True, null=True)
  insert_size = models.IntegerField(blank=True, null=True)
  notes = models.TextField(blank=True)

  bioanalyzer_summary = models.TextField(blank=True,default="")
  bioanalyzer_concentration = models.DecimalField(max_digits=5, 
                                decimal_places=2, blank=True, null=True,
                                help_text=u"(ng/\u00b5l)")
  bioanalyzer_image_url = models.URLField(blank=True,default="")
  
  def __unicode__(self):
    return u'#%s: %s' % (self.id, self.library_name)
  
  class Meta:
      verbose_name_plural = "libraries"
      #ordering = ["-creation_date"] 
      ordering = ["-id"]
  
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
    
  def is_archived(self):
    """
    returns True if archived else False
    """
    if self.longtermstorage_set.count() > 0:
        return True
    else:
        return False

  def stopping_point_name(self):
      end_points = Library.PROTOCOL_END_POINTS_DICT
      name = end_points.get(self.stopping_point, None)
      if name is None:
          name = "Lookup Error"
          logger.error("protocol stopping point in database didn't match names in library model")
      return name
      

  def libtags(self):
    affs = self.tags.all().order_by('tag_name')
    ar = []
    for t in affs:
      ar.append(t.__unicode__())
    return u'%s' % ( ", ".join(ar))

  def DataRun(self):
    str ='<a target=_self href="/admin/experiments/datarun/?q='+self.id+'" title="Check All Data Runs for This Specific Library ..." ">Data Run</a>' 
    return str
  DataRun.allow_tags = True

  def aligned_m_reads(self):
    return getLibReads(self.id)

  def aligned_reads(self):
    res = getLibReads(self.id)

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
  
  def public(self):
    SITE_ROOT = '/'
    summary_url = self.get_absolute_url()
    return '<a href="%s">S</a>' % (summary_url,)
  public.allow_tags = True
    
  @models.permalink
  def get_absolute_url(self):
    return ('htsworkflow.frontend.samples.views.library_to_flowcells', [str(self.id)])


class HTSUser(User):
    """
    Provide some site-specific customization for the django user class
    """
    #objects = UserManager()

    class Meta:
        ordering = ['first_name', 'last_name', 'username']

    def admin_url(self):
        return '/admin/%s/%s/%d' % (self._meta.app_label, self._meta.module_name, self.id)

    def __unicode__(self):
        #return unicode(self.username) + u" (" + unicode(self.get_full_name()) + u")"
        return unicode(self.get_full_name()) + u' (' + unicode(self.username) + ')'
    
def HTSUserInsertID(sender, instance, **kwargs):
    """
    Force addition of HTSUsers when someone just modifies the auth_user object
    """
    u = HTSUser.objects.filter(pk=instance.id)
    if len(u) == 0:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO samples_htsuser (user_ptr_id) VALUES (%s);' % (instance.id,))
        cursor.close()
    
post_save.connect(HTSUserInsertID, sender=User)
