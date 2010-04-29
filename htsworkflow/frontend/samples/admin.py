from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.admin.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.template import Context, Template
from django.db import models
from django.utils.translation import ugettext_lazy as _

from htsworkflow.frontend.samples.models import Antibody, Cellline, Condition, ExperimentType, HTSUser, LibraryType, Species, Affiliation, Library, Tag
from htsworkflow.frontend.experiments.models import Lane
from htsworkflow.frontend.inventory.models import PrinterTemplate
from htsworkflow.frontend.bcmagic.utils import print_zpl_socket

class AffiliationOptions(admin.ModelAdmin):
    list_display = ('name','contact','email')
    fieldsets = (
      (None, {
          'fields': (('name','contact','email','users'))
      }),
    )

    # some post 1.0.2 version of django has formfield_overrides 
    # which would replace this code with:
    # formfield_overrids = {
    #   models.ManyToMany: { 'widget': widgets.FilteredSelectMultiple }
    # }
    def formfield_for_dbfield(self, db_field, **kwargs):
      if db_field.name == 'users':
        kwargs['widget'] = widgets.FilteredSelectMultiple(db_field.verbose_name, (db_field.name in self.filter_vertical))
      rv = super(AffiliationOptions, self).formfield_for_dbfield(db_field, **kwargs)
    #  print db_field.name, kwargs
      return rv

class AntibodyOptions(admin.ModelAdmin):
    search_fields = ('antigene','nickname','catalog','antibodies','source','biology','notes')
    list_display = ('antigene','nickname','antibodies','catalog','source','biology','notes')
    list_filter = ('antibodies','source')
    fieldsets = (
      (None, {
          'fields': (('antigene','nickname','antibodies'),('catalog','source'),('biology'),('notes'))
      }),
     )

class CelllineOptions(admin.ModelAdmin):
    list_display = ('cellline_name', 'nickname', 'notes')
    search_fields = ('cellline_name', 'nickname', 'notes')
    fieldsets = (
      (None, {
          'fields': (('cellline_name'),('notes'),)
      }),
     )

class ConditionOptions(admin.ModelAdmin):
    list_display = (('condition_name'), ('notes'),)
    fieldsets = (
      (None, {
          'fields': (('condition_name'),('nickname'),('notes'),)
      }),
     )

class ExperimentTypeOptions(admin.ModelAdmin):
  model = ExperimentType
  #list_display = ('name',)
  #fieldsets = ( (None, { 'fields': ('name',) }), )

class HTSUserCreationForm(UserCreationForm):
    class Meta:
        model = HTSUser
        fields = ("username",'first_name','last_name')

class HTSUserChangeForm(UserChangeForm):
    class Meta:
        model = HTSUser
        
class HTSUserOptions(UserAdmin):
    form = HTSUserChangeForm
    add_form = HTSUserCreationForm

class LaneLibraryInline(admin.StackedInline):
  model = Lane
  extra = 0

class Library_Inline(admin.TabularInline):
  model = Library

class LibraryTypeOptions(admin.ModelAdmin):
    model = LibraryType

class LibraryOptions(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("css/wide_account_number.css",)
            }
        
    date_hierarchy = "creation_date"
    save_as = True
    save_on_top = True
    search_fields = (
        'id',
        'library_name',
        'cell_line__cellline_name',
        'library_species__scientific_name',
        'library_species__common_name',
    )
    list_display = (
        'id',
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
        'stopping_point',
        'hidden')
    list_display_links = ('id', 'library_name',)
    fieldsets = (
      (None, {
        'fields': (
          ('id','library_name','hidden'),
          ('library_species'),
          ('library_type', 'experiment_type', 'replicate'),
          ('cell_line','condition','antibody'),)
         }),
         ('Creation Information:', {
             'fields' : (('made_for', 'made_by', 'creation_date'), ('stopping_point', 'amplified_from_sample'), ('avg_lib_size','undiluted_concentration', 'ten_nM_dilution', 'successful_pM'), 'account_number', 'notes',)
         }),
         ('Library/Project Affiliation:', {
             'fields' : (('affiliations'), ('tags'),)
         }),
         )
    inlines = [
      LaneLibraryInline,
    ]
    actions = ['action_print_library_labels']
    
    
    def action_print_library_labels(self, request, queryset):
        """
        Django action which prints labels for the selected set of labels from the
        Django Admin interface.
        """
        
        #Probably should ask if the user really meant to print all selected
        # libraries if the count is above X. X=10 maybe?
        
        # Grab the library template
        #FIXME: Hardcoding library template name. Not a good idea... *sigh*.
        EVIL_HARDCODED_LIBRARY_TEMPLATE_NAME = "Library"
        
        try:
            template = PrinterTemplate.objects.get(item_type__name=EVIL_HARDCODED_LIBRARY_TEMPLATE_NAME)
        except PrinterTemplate.DoesNotExist:
            self.message_user(request, "Could not find a library template with ItemType.name of '%s'" % \
                              (EVIL_HARDCODED_LIBRARY_TEMPLATE_NAME))
            return
        
        # ZPL Template
        t = Template(template.template)
        
        #Iterate over selected labels to print
        for library in queryset.all():
            
            # Django Template Context
            c = Context({'library': library})
            
            # Send rendered template to the printer that the template
            #  object has been attached to in the database.
            print_zpl_socket(t.render(c), host=template.printer.ip_address)
    
        self.message_user(request, "%s labels printed." % (len(queryset)))
                          
    action_print_library_labels.short_description = "Print Labels"



    # some post 1.0.2 version of django has formfield_overrides 
    # which would replace this code with:
    # formfield_overrids = {
    #    models.ManyToMany: { 'widget': widgets.FilteredSelectMultiple }
    #}
    def formfield_for_dbfield(self, db_field, **kwargs):
      if db_field.name in ('affiliations', 'tags'):
        kwargs['widget'] = widgets.FilteredSelectMultiple(db_field.verbose_name,
                                                          (db_field.name in self.filter_vertical))
      rv = super(LibraryOptions, self).formfield_for_dbfield(db_field, **kwargs)
      return rv

class SpeciesOptions(admin.ModelAdmin):
    fieldsets = (
      (None, {
          'fields': (('scientific_name', 'common_name'),)
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
admin.site.register(ExperimentType, ExperimentTypeOptions)
admin.site.register(HTSUser, HTSUserOptions)
admin.site.register(LibraryType, LibraryTypeOptions)
admin.site.register(Library, LibraryOptions)
admin.site.register(Species, SpeciesOptions)
admin.site.register(Tag, TagOptions)
