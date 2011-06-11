from htsworkflow.frontend.experiments.models import \
     FlowCell, DataRun, DataFile, FileType, ClusterStation, Sequencer, Lane
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django.forms.fields import Field, CharField
from django.forms.widgets import TextInput
from django.utils.translation import ugettext_lazy as _

class DataFileForm(ModelForm):
    class Meta:
        model = DataFile

class DataFileInline(admin.TabularInline):
    model = DataFile
    form = DataFileForm
    raw_id_fields = ('library',)
    extra = 0

class DataRunOptions(admin.ModelAdmin):
  search_fields = [
      'flowcell_id',
      'run_folder',
      'run_note',
      ]
  list_display = [
      'runfolder_name',
      'result_dir',
      'run_start_time',
  ]
  fieldsets = (
      (None, {
        'fields': (('flowcell', 'run_status'),
                   ('runfolder_name', 'cycle_start', 'cycle_stop'),
                   ('result_dir',),
                   ('last_update_time'),
                   ('comment',))
      }),
    )
  inlines = [ DataFileInline ]
  #list_filter = ('run_status', 'run_start_time')
admin.site.register(DataRun, DataRunOptions)


class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'mimetype', 'regex')
admin.site.register(FileType, FileTypeAdmin)
  
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
admin.site.register(Lane, LaneOptions)
    
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
          'fields': ('run_date', ('flowcell_id','cluster_station','sequencer'),
                    ('read_length', 'control_lane', 'paired_end'),)
        }),
        ('Notes:', { 'fields': ('notes',),}),
    )
    inlines = [
      LaneInline,
    ]

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(FlowCellOptions, self).formfield_for_dbfield(db_field,
                                                                   **kwargs)
        # Override field attributes
        if db_field.name == "notes":
            field.widget.attrs["rows"] = "3"
        return field
admin.site.register(FlowCell, FlowCellOptions)

class ClusterStationOptions(admin.ModelAdmin):
    list_display = ('name', )
    fieldsets = ( ( None, { 'fields': ( 'name', ) } ), )
admin.site.register(ClusterStation, ClusterStationOptions)

class SequencerOptions(admin.ModelAdmin):
    list_display = ('name', )
    fieldsets = ( ( None, { 'fields': ( 'name', ) } ), )
admin.site.register(Sequencer, SequencerOptions)
