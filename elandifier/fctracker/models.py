from django.db import models
from elandifier import settings

# Create your models here.


class Specie(models.Model):
  
  class Admin: pass
  
  scientific_name = models.CharField(maxlength=256, unique=True, db_index=True)


  def __str__(self):
    return self.scientific_name

#class BedFilePack(models.Model):

class Library(models.Model):
  class Admin: pass
  
  library_id = models.IntegerField(unique=True, db_index=True)
  library_name = models.CharField(maxlength=100, unique=True)
  library_species = models.ForeignKey(Specie)
  
  made_from_sample = models.ForeignKey('self', blank=True)
  
  made_by = models.CharField(maxlength=50, blank=True)
  creation_date = models.DateField(blank=True, null=True)
  notes = models.TextField(blank=True)
  
  def __str__(self):
    return self.library_name


class FlowCell(models.Model):
  
  class Admin: pass
  
  flowcell_id = models.CharField(maxlength=20, unique=True, db_index=True)
  
  run_date = models.DateTimeField()
  
  lane1_sample = models.CharField(maxlength=500)
  lane1_species = models.ForeignKey(Specie, related_name="lane1_species")
  lane2_sample = models.CharField(maxlength=500)
  lane2_species = models.ForeignKey(Specie, related_name="lane2_species")
  lane3_sample = models.CharField(maxlength=500)
  lane3_species = models.ForeignKey(Specie, related_name="lane3_species")
  lane4_sample = models.CharField(maxlength=500)
  lane4_species = models.ForeignKey(Specie, related_name="lane4_species")
  
  lane5_sample = models.CharField(maxlength=500)
  lane5_species = models.ForeignKey(Specie, related_name="lane5_species")
  lane6_sample = models.CharField(maxlength=500)
  lane6_species = models.ForeignKey(Specie, related_name="lane6_species")
  lane7_sample = models.CharField(maxlength=500)
  lane7_species = models.ForeignKey(Specie, related_name="lane7_species")
  lane8_sample = models.CharField(maxlength=500)
  lane8_species = models.ForeignKey(Specie, related_name="lane8_species")
  
  notes = models.TextField(blank=True)

  def __str__(self):
    return self.flowcell_id


class ElandResult(models.Model):
  
  class Admin: pass
  
  flow_cell = models.ForeignKey(FlowCell)
  config_file = models.FileField(upload_to=settings.UPLOADTO_CONFIG_FILE)
  eland_result_pack = models.FileField(upload_to=settings.UPLOADTO_ELAND_RESULT_PACKS)
  bed_file_pack = models.FileField(upload_to=settings.UPLOADTO_BED_PACKS)
  
  notes = models.TextField(blank=True)
