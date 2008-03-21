from django.db import models
from gaworkflow.frontend import settings

# Create your models here.

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

class Person(models.Model):

  name = models.CharField(max_length=100, primary_key=True, db_index=True)
  lab = models.CharField(max_length=100)
  email = models.CharField(max_length=50, blank=True, null=True)
  
  def __str__(self):
    return '%s (%s lab)' % (self.name, self.lab)
  
  class Meta:
    verbose_name_plural = "people"
    ordering = ["lab"]
    
  class Admin:
    fields = (
      (None, {
          'fields': (('name', 'lab'), ('email'))
      }),
    )


class Library(models.Model):
  
  library_id = models.CharField(max_length=25, primary_key=True, db_index=True, core=True)
  library_name = models.CharField(max_length=100, unique=True, core=True)
  library_species = models.ForeignKey(Species, core=True)
  #use_genome_build = models.CharField(max_length=100, blank=False, null=False)
  RNAseq = models.BooleanField()
  
  made_by = models.CharField(max_length=50, blank=True, default="Lorian")
  creation_date = models.DateField(blank=True, null=True)
  made_for = models.ForeignKey(Person)
  
  PROTOCOL_END_POINTS = (
      ('?', 'Unknown'),
      ('Sample', 'Raw sample'),
      ('Gel', 'Ran gel'),
      ('1A', 'Gel purification'),
      ('2A', '2nd PCR'),
      ('Done', 'Completed'),
      ('Progress', 'In progress'),
    )
  stopping_point = models.CharField(max_length=50, choices=PROTOCOL_END_POINTS)
  amplified_from_sample = models.ForeignKey('self', blank=True, null=True)
  library_size = models.IntegerField(default=225, blank=True, null=True)
  
  undiluted_concentration = models.DecimalField("Undiluted concentration (ng/ul)", max_digits=5, decimal_places=2, default=0)
  successful_pM = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
  
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
    list_display = ('library_id', 'library_name', 'made_for', 'library_species', 'creation_date')
    list_display_links = ('library_id', 'library_name')
    list_filter = ('stopping_point', 'library_species', 'made_for', 'made_by')
    fields = (
        (None, {
            'fields': (('library_id', 'library_name'), ('library_species', 'RNAseq'),)
        }),
        ('Creation Information:', {
            'fields' : (('made_for', 'made_by', 'creation_date'), ('stopping_point', 'amplified_from_sample'), ('undiluted_concentration', 'library_size'), 'notes',)
        }),
	('Run Information:', {
	    'fields' : (('successful_pM'),)
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
    )

class ElandResult(models.Model):
  
  class Admin: pass
  
  flow_cell = models.ForeignKey(FlowCell)
  config_file = models.FileField(upload_to=settings.UPLOADTO_CONFIG_FILE)
  eland_result_pack = models.FileField(upload_to=settings.UPLOADTO_ELAND_RESULT_PACKS)
  bed_file_pack = models.FileField(upload_to=settings.UPLOADTO_BED_PACKS)
  
  notes = models.TextField(blank=True)
