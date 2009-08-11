from htsworkflow.frontend.experiments.models import FlowCell, DataRun, ClusterStation, Sequencer, Lane
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class LaneInline(admin.StackedInline):
  model = Lane
  max_num = 8
  extra = 8

class DataRunOptions(admin.ModelAdmin):
  search_fields = [
      'run_folder',
      'run_note',
      'config_params',
      '=fcid__lane_1_library__library_id',
      '=fcid__lane_2_library__library_id',
      '=fcid__lane_3_library__library_id',
      '=fcid__lane_4_library__library_id',
      '=fcid__lane_5_library__library_id',
      '=fcid__lane_6_library__library_id',
      '=fcid__lane_7_library__library_id',
      '=fcid__lane_8_library__library_id'
      'fcid__lane_1_library__library_name',
      'fcid__lane_2_library__library_name',
      'fcid__lane_3_library__library_name',
      'fcid__lane_4_library__library_name',
      'fcid__lane_5_library__library_name',
      'fcid__lane_6_library__library_name',
      'fcid__lane_7_library__library_name',
      'fcid__lane_8_library__library_name'  ]
  list_display = [
      'run_folder', 
      'Flowcell_Info', 
      'run_start_time',
      'main_status', 
      'run_note',
  ]
  list_filter = ('run_status', 'run_start_time')

class FlowCellOptions(admin.ModelAdmin):
    date_hierarchy = "run_date"
    save_on_top = True
    search_fields = ('flowcell_id',
        'sequencer__name',
        'cluster_station__name',
        '=lane__library__library_id',
        'lane__library__library_name')
    list_display = ('flowcell_id','run_date','Lanes')
    list_filter = ('sequencer','cluster_station')
    fieldsets = (
        (None, {
            'fields': ('run_date', ('flowcell_id','cluster_station','sequencer'), ('read_length', 'paired_end'),)
        }),
        #('Lanes:', {
        #   'fields' : (('lane__library__library_id', 'lane__pM', 'lane__cluster_estimate'),)
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
    
class LaneOptions(admin.ModelAdmin):
    list_display = ('flowcell', 'lane_number', 'library', 'comment')
    fieldsets = (
      (None, {
        'fields': ('lane_number', 'flowcell', 'library', 'pM', 'cluster_estimate')
      }),
      ('Optional', {
        'classes': ('collapse', ),
        'fields': ('comment', )
      }),
    )
    

admin.site.register(DataRun, DataRunOptions)
admin.site.register(FlowCell, FlowCellOptions)
admin.site.register(ClusterStation, ClusterStationOptions)
admin.site.register(Sequencer, SequencerOptions)
admin.site.register(Lane, LaneOptions)
