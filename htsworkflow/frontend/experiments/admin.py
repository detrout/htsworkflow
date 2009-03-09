from htsworkflow.frontend.experiments.models import FlowCell, DataRun, ClusterStation, Sequencer
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

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
  ]
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
        'sequencer',
        'cluster_station',
        '=lane_1_library__library_id',
        '=lane_2_library__library_id',
        '=lane_3_library__library_id',
        '=lane_4_library__library_id',
        '=lane_5_library__library_id',
        '=lane_6_library__library_id',
        '=lane_7_library__library_id',
        '=lane_8_library__library_id')
    list_display = ('flowcell_id','run_date','Lanes')
    list_filter = ('sequencer','cluster_station')
    fieldsets = (
        (None, {
            'fields': ('run_date', ('flowcell_id','cluster_station','sequencer'), ('read_length', 'paired_end'),)
        }),
        ('Lanes:', {
           'fields' : (('lane_1_library', 'lane_1_pM', 'lane_1_cluster_estimate'), ('lane_2_library', 'lane_2_pM', 'lane_2_cluster_estimate'), ('lane_3_library', 'lane_3_pM', 'lane_3_cluster_estimate'), ('lane_4_library', 'lane_4_pM', 'lane_4_cluster_estimate'), ('lane_5_library', 'lane_5_pM', 'lane_5_cluster_estimate'), ('lane_6_library', 'lane_6_pM', 'lane_6_cluster_estimate'), ('lane_7_library', 'lane_7_pM', 'lane_7_cluster_estimate'), ('lane_8_library', 'lane_8_pM', 'lane_8_cluster_estimate'),)
        }),
        ('Notes:', { 'fields': ('notes',),}),
    )

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
