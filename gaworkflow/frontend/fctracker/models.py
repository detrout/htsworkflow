from django.db import models
from django.contrib.auth.models import User
from gaworkflow.frontend import settings

# Create your models here.

class Antibody(models.Model):
  antigene = models.CharField(max_length=500, db_index=True)
  catalog = models.CharField(max_length=50, unique=True, db_index=True)
  antibodies = models.CharField(max_length=500, db_index=True)
  source = models.CharField(max_length=500, blank=True, db_index=True)
  biology = models.TextField(blank=True)
  notes = models.TextField(blank=True)
  def __str__(self):
    return '%s - %s (%s)' % (self.antigene, self.antibodies, self.catalog)
  class Meta:
    verbose_name_plural = "antibodies"
    ordering = ["antigene"]
  class Admin:
      list_display = ('antigene','antibodies','catalog','source','biology','notes')
      list_filter = ('antibodies','source')
      fields = (
        (None, {
            'fields': (('antigene','antibodies'),('catalog','source'),('biology'),('notes'))
        }),
       )

class Cellline(models.Model):
  cellline_name = models.CharField(max_length=100, unique=True, db_index=True)
  notes = models.TextField(blank=True)
  def __str__(self):
    return '%s' % (self.cellline_name)

  class Meta:
    ordering = ["cellline_name"]

  class Admin:
      fields = (
        (None, {
            'fields': (('cellline_name'),('notes'),)
        }),
       )

class Condition(models.Model):
  condition_name = models.CharField(max_length=2000, unique=True, db_index=True)
  notes = models.TextField(blank=True)
  def __str__(self):
    return '%s' % (self.condition_name)

  class Meta:
    ordering = ["condition_name"]

  class Admin:
      fields = (
        (None, {
            'fields': (('condition_name'),('notes'),)
        }),
       )

class Species(models.Model):
  
  scientific_name = models.CharField(max_length=256, unique=False, db_index=True, core=True)
  common_name = models.CharField(max_length=256, blank=True)
  use_genome_build = models.CharField(max_length=100, blank=False, null=False)

  def __str__(self):
    return '%s (%s)|%s' % (self.scientific_name, self.common_name, self.use_genome_build)
  
  class Meta:
    verbose_name_plural = "species"
    ordering = ["scientific_name"]
  
  class Admin:
      fields = (
        (None, {
            'fields': (('scientific_name', 'common_name'), ('use_genome_build'))
        }),
      )

class Lab(models.Model):
  
  name = models.CharField(max_length=100, blank=False, unique=True)
  
  def __str__(self):
    return self.name
  
  class Admin:
    pass

class UserProfile(models.Model):
  
  # This allows you to use user.get_profile() to get this object
  user = models.ForeignKey(User, unique=True)

  lab = models.ForeignKey(Lab)
  #email = models.CharField(max_length=50, blank=True, null=True)
  
  def __str__(self):
    return '%s (%s lab)' % (self.user, self.lab)
  
  class Meta:
    #verbose_name_plural = "people"
    #ordering = ["lab"]
    pass
    
  class Admin:
    #fields = (
    #  (None, {
    #      'fields': (('email', 'lab'), ('email'))
    #  }),
    #)
    pass


class Library(models.Model):
  
  library_id = models.CharField(max_length=30, primary_key=True, db_index=True, core=True)
  library_name = models.CharField(max_length=100, unique=True, core=True)
  library_species = models.ForeignKey(Species, core=True)
  cell_line = models.ForeignKey(Cellline,core=True)
  condition = models.ForeignKey(Condition,core=True)
  antibody = models.ForeignKey(Antibody,blank=True,null=True,core=True)
  
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
  made_for = models.ForeignKey(User)
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
  
  def __str__(self):
    return '#%s: %s' % (self.library_id, self.library_name)
  
  class Meta:
    verbose_name_plural = "libraries"
    ordering = ["-library_id"]
  
  class Admin:
    date_hierarchy = "creation_date"
    save_as = True
    save_on_top = True
    search_fields = ['library_name', 'library_id']
    list_display = ('library_id', 'library_name', 'made_for', 'creation_date', 'stopping_point')
    list_display_links = ('library_id', 'library_name')
    list_filter = ('stopping_point', 'library_species', 'made_for', 'made_by', 'experiment_type')
    fields = (
        (None, {
            'fields': (('library_id', 'library_name'), ('library_species', 'experiment_type'),)
        }),
        ('Creation Information:', {
            'fields' : (('made_for', 'made_by', 'creation_date'), ('stopping_point', 'amplified_from_sample'), ('undiluted_concentration', 'library_size'), 'notes',)
        }),
	('Run Information:', {
	    'fields' : (('ten_nM_dilution','successful_pM'),)
	}),
    )

class FlowCell(models.Model):
  
  flowcell_id = models.CharField(max_length=20, unique=True, db_index=True, core=True)
  run_date = models.DateTimeField(core=True)
  advanced_run = models.BooleanField(default=False)
  read_length = models.IntegerField(default=32)
  
  
  FLOWCELL_STATUSES = (
      ('No', 'Not run'),
      ('F', 'Failed'),
      ('Del', 'Data deleted'),
      ('A', 'Data available'),
      ('In', 'In progress'),
    )
  flowcell_status = models.CharField(max_length=10, choices=FLOWCELL_STATUSES)
  
  lane_1_library = models.ForeignKey(Library, related_name="lane_1_library")
  lane_2_library = models.ForeignKey(Library, related_name="lane_2_library")
  lane_3_library = models.ForeignKey(Library, related_name="lane_3_library")
  lane_4_library = models.ForeignKey(Library, related_name="lane_4_library")
  lane_5_library = models.ForeignKey(Library, related_name="lane_5_library")
  lane_6_library = models.ForeignKey(Library, related_name="lane_6_library")
  lane_7_library = models.ForeignKey(Library, related_name="lane_7_library")
  lane_8_library = models.ForeignKey(Library, related_name="lane_8_library")

  lane_1_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_2_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_3_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_4_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_5_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_6_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_7_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  lane_8_pM = models.DecimalField(max_digits=5, decimal_places=2, default=4)
  
  lane_1_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_2_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_3_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_4_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_5_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_6_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_7_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  lane_8_cluster_estimate = models.CharField(max_length=25, blank=True, null=True)
  
  kit_1000148 = models.IntegerField(blank=True, null=True)
  kit_1000147 = models.IntegerField(blank=True, null=True)
  kit_1000183 = models.IntegerField(blank=True, null=True)
  kit_1001625 = models.IntegerField(blank=True, null=True)
  
  cluster_station_id = models.CharField(max_length=50, blank=True, null=True)
  sequencer_id = models.CharField(max_length=50, blank=True, null=True)
  
  notes = models.TextField(blank=True)

  def __str__(self):
    return '%s (%s)' % (self.flowcell_id, self.run_date) 
  
  class Meta:
    ordering = ["-run_date"]
  
  class Admin:
    date_hierarchy = "run_date"
    save_as = True
    save_on_top = True
    search_fields = ['flowcell_id', 'lane_1_library__library_id', 'lane_1_library__library_name', 'lane_2_library__library_id', 'lane_2_library__library_name', 'lane_3_library__library_id', 'lane_3_library__library_name', 'lane_4_library__library_id', 'lane_4_library__library_name', 'lane_5_library__library_id', 'lane_5_library__library_name', 'lane_6_library__library_id', 'lane_6_library__library_name', 'lane_7_library__library_id', 'lane_7_library__library_name', 'lane_8_library__library_id', 'lane_8_library__library_name']
    list_display = ('run_date', 'flowcell_status', 'flowcell_id', 'lane_1_library', 'lane_2_library', 'lane_3_library', 'lane_4_library', 'lane_5_library', 'lane_6_library', 'lane_7_library', 'lane_8_library')
    list_display_links = ('run_date', 'flowcell_id', 'lane_1_library', 'lane_2_library', 'lane_3_library', 'lane_4_library', 'lane_5_library', 'lane_6_library', 'lane_7_library', 'lane_8_library')
    fields = (
        (None, {
            'fields': ('run_date', ('flowcell_id', 'flowcell_status'), ('read_length', 'advanced_run'),)
        }),
        ('Lanes:', {
            'fields' : (('lane_1_library', 'lane_1_pM'), ('lane_2_library', 'lane_2_pM'), ('lane_3_library', 'lane_3_pM'), ('lane_4_library', 'lane_4_pM'), ('lane_5_library', 'lane_5_pM'), ('lane_6_library', 'lane_6_pM'), ('lane_7_library', 'lane_7_pM'), ('lane_8_library', 'lane_8_pM'),)
        }),
	(None, {
	    'fields' : ('notes',)
	}),
	('Kits & Machines:', {
	    'classes': 'collapse',
	    'fields' : (('kit_1000148', 'kit_1000147', 'kit_1000183', 'kit_1001625'), ('cluster_station_id', 'sequencer_id'),)
	}),
	('Cluster Estimates:', {
	    'classes': 'collapse',
	    'fields' : (('lane_1_cluster_estimate', 'lane_2_cluster_estimate'), ('lane_3_cluster_estimate', 'lane_4_cluster_estimate'), ('lane_5_cluster_estimate', 'lane_6_cluster_estimate'), ('lane_7_cluster_estimate', 'lane_8_cluster_estimate',),)
	}),
    )

# Did not finish implementing, removing to avoid further confusion.
#class ElandResult(models.Model):
#  
#  class Admin: pass
#  
#  flow_cell = models.ForeignKey(FlowCell)
#  config_file = models.FileField(upload_to=settings.UPLOADTO_CONFIG_FILE)
#  eland_result_pack = models.FileField(upload_to=settings.UPLOADTO_ELAND_RESULT_PACKS)
#  bed_file_pack = models.FileField(upload_to=settings.UPLOADTO_BED_PACKS)
#  
#  notes = models.TextField(blank=True)
