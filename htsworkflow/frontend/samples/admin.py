from htsworkflow.frontend.samples.models import Antibody, Cellline, Condition, Species, Affiliation, Library, Tag
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class Library_Inline(admin.TabularInline):
  model = Library

class CelllineOptions(admin.ModelAdmin):
    list_display = ('cellline_name', 'nickname', 'notes')
    search_fields = ('cellline_name', 'nickname', 'notes')
    fieldsets = (
      (None, {
          'fields': (('cellline_name'),('notes'),)
      }),
     )

class LibraryOptions(admin.ModelAdmin):
    date_hierarchy = "creation_date"
    save_as = True
    save_on_top = True
    search_fields = (
        'library_id',
        'library_name',
        'cell_line__cellline_name',
        'library_species__scientific_name',
        'library_species__common_name',
    )
    list_display = (
        'library_id',
        #'aligned_reads',
        #'DataRun',
        'library_name',
        'public',
        #'experiment_type',
        #'organism',
        #'antibody_name',
        #'cell_line',
        #'libtags',
        #'made_for',
        'affiliation',
        #'made_by',
        'undiluted_concentration',
        'creation_date',
        'stopping_point',
        #'condition',

    )
    list_filter = (
        'experiment_type', 
        'library_species', 
        'tags',
        #'made_for',
        'affiliations',
        'made_by', 
        'antibody',
        'cell_line',
        'condition',
        'stopping_point')
    list_display_links = ('library_id', 'library_name',)
    fieldsets = (
      (None, {
        'fields': (
          ('replicate','library_id','library_name'),
          ('library_species'),
          ('experiment_type'),
          ('cell_line','condition','antibody'),)
         }),
         ('Creation Information:', {
             'fields' : (('made_for', 'made_by', 'creation_date'), ('stopping_point', 'amplified_from_sample'), ('avg_lib_size','undiluted_concentration', 'ten_nM_dilution', 'successful_pM'), 'notes',)
         }),
         ('Library/Project Affiliation:', {
             'fields' : (('affiliations'), ('tags'),)
         }),
         )

class AffiliationOptions(admin.ModelAdmin):
    list_display = ('name','contact','email')
    fieldsets = (
      (None, {
          'fields': (('name','contact','email'))
      }),
    )

# class UserOptions(admin.ModelAdmin):
#   inlines = [Library_Inline]

class AntibodyOptions(admin.ModelAdmin):
    search_fields = ('antigene','nickname','catalog','antibodies','source','biology','notes')
    list_display = ('antigene','nickname','antibodies','catalog','source','biology','notes')
    list_filter = ('antibodies','source')
    fieldsets = (
      (None, {
          'fields': (('antigene','nickname','antibodies'),('catalog','source'),('biology'),('notes'))
      }),
     )

class SpeciesOptions(admin.ModelAdmin):
    fieldsets = (
      (None, {
          'fields': (('scientific_name', 'common_name'),)
      }),
    )

class ConditionOptions(admin.ModelAdmin):
    list_display = (('condition_name'), ('notes'),)
    fieldsets = (
      (None, {
          'fields': (('condition_name'),('nickname'),('notes'),)
      }),
     )

class TagOptions(admin.ModelAdmin):
    list_display = ('tag_name', 'context')
    fieldsets = ( 
        (None, {
          'fields': ('tag_name', 'context')
          }),
        )

admin.site.register(Affiliation, AffiliationOptions)
admin.site.register(Antibody, AntibodyOptions)
admin.site.register(Cellline, CelllineOptions)
admin.site.register(Condition, ConditionOptions)
admin.site.register(Library, LibraryOptions)
admin.site.register(Species, SpeciesOptions)
admin.site.register(Tag, TagOptions)
