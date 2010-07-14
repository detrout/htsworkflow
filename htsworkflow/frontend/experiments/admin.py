from htsworkflow.frontend.experiments.models import FlowCell, DataRun, ClusterStation, Sequencer, Lane
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django.forms.fields import Field, CharField
from django.forms.widgets import TextInput
from django.utils.translation import ugettext_lazy as _

class DataRunOptions(admin.ModelAdmin):
  search_fields = [
      'run_folder',
      'run_note',
      'config_params', ]
  list_display = [
      'run_folder', 
      'Flowcell_Info', 
      'run_start_time',
      'main_status', 
      'run_note',
  ]
  list_filter = ('run_status', 'run_start_time')

# lane form setup needs to come before Flowcell form config
# as flowcell refers to the LaneInline class
class LaneForm(ModelForm):
    comment = CharField(widget=TextInput(attrs={'size':'80'}), required=False)
    
    class Meta:
        model = Lane

class LaneInline(admin.StackedInline):
    """
    Controls display of Lanes on the Flowcell form.
    """
    model = Lane
    max_num = 8
    extra = 8
    form = LaneForm
    raw_id_fields = ('library',)
    fieldsets = (
      (None, {
        'fields': ('lane_number', 'flowcell',
                   ('library',),
                   ('pM', 'cluster_estimate', 'status'),
                   'comment',)
      }),
    )

class LaneOptions(admin.ModelAdmin):
    """
    Controls display of Lane browser
    """
    search_fields = ('=flowcell__flowcell_id', 'library__id', 'library__library_name' )
    list_display = ('flowcell', 'lane_number', 'library', 'comment')
    fieldsets = (
      (None, {
        'fields': ('lane_number', 'flowcell',
                   ('library'),
                   ('pM', 'cluster_estimate'))
      }),
      ('Optional', {
        'classes': ('collapse', ),
        'fields': ('comment', )
      }),
    )
    
class FlowCellOptions(admin.ModelAdmin):
    date_hierarchy = "run_date"
    save_on_top = True
    search_fields = ('flowcell_id',
        'sequencer__name',
        'cluster_station__name',
        '=lane__library__id',
        'lane__library__library_name')
    list_display = ('flowcell_id','run_date','Lanes')
    list_filter = ('sequencer','cluster_station')
    fieldsets = (
        (None, {
            'fields': ('run_date', ('flowcell_id','cluster_station','sequencer'), ('read_length', 'control_lane', 'paired_end'),)
        }),
        #('Lanes:', {
        #   'fields' : (('lane__library__id', 'lane__pM', 'lane__cluster_estimate'),)
        #}),
        ('Notes:', { 'fields': ('notes',),}),
    )
    inlines = [
      LaneInline,
    ]

class ClusterStationOptions(admin.ModelAdmin):
    list_display = ('name', )
    fieldsets = ( ( None, { 'fields': ( 'name', ) } ), )

class SequencerOptions(admin.ModelAdmin):
    list_display = ('name', )
    fieldsets = ( ( None, { 'fields': ( 'name', ) } ), )
    

admin.site.register(DataRun, DataRunOptions)
admin.site.register(FlowCell, FlowCellOptions)
admin.site.register(ClusterStation, ClusterStationOptions)
admin.site.register(Sequencer, SequencerOptions)
admin.site.register(Lane, LaneOptions)
