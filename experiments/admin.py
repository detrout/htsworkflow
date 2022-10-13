from __future__ import absolute_import, print_function, unicode_literals

from django.contrib import admin
from django.forms import ModelForm
from django.forms.fields import CharField
from django.forms.widgets import TextInput, Select
from django.utils.encoding import force_str
from django.utils.html import escape, conditional_escape

from .models import (
    FlowCell,
    SequencingRun,
    DataFile,
    FileType,
    ClusterStation,
    Sequencer,
    Lane
)


class DataFileForm(ModelForm):
    class Meta:
        model = DataFile
        fields = ('random_key', 'sequencing_run', 'library',
                  'file_type', 'relative_pathname')


class DataFileInline(admin.TabularInline):
    model = DataFile
    form = DataFileForm
    raw_id_fields = ('library',)
    extra = 0


@admin.register(SequencingRun)
class SequencingRunOptions(admin.ModelAdmin):
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
            'fields': (
                ('flowcell', 'run_status'),
                ('runfolder_name', 'cycle_start', 'cycle_stop'),
                ('result_dir',),
                ('last_update_time'),
                ('image_software', 'image_version'),
                ('basecall_software', 'basecall_version'),
                ('alignment_software', 'alignment_version'),
                ('comment',))
        }),
    )
    inlines = [DataFileInline]
    # list_filter = ('run_status', 'run_start_time')


@admin.register(FileType)
class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'mimetype', 'regex')


# lane form setup needs to come before Flowcell form config
# as flowcell refers to the LaneInline class
class LaneForm(ModelForm):
    comment = CharField(
        widget=TextInput(attrs={'size': '80'}),
        required=False)

    class Meta:
        model = Lane
        fields = ('flowcell', 'lane_number', 'library',
                  'pM', 'cluster_estimate',
                  'status', 'comment')


class LaneInline(admin.StackedInline):
    """Controls display of Lanes on the Flowcell form.
    """
    model = Lane
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


@admin.register(Lane)
class LaneOptions(admin.ModelAdmin):
    """Controls display of Lane browser
    """
    search_fields = (
        '=flowcell__flowcell_id',
        'library__id',
        'library__library_name')
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


@admin.register(FlowCell)
class FlowCellOptions(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/admin_flowcell.css',)}
    date_hierarchy = "run_date"
    save_on_top = True
    search_fields = (
        'flowcell_id',
        'sequencer__name',
        'cluster_station__name',
        '=lane__library__id',
        'lane__library__library_name')
    list_display = ('flowcell_id', 'run_date', 'Lanes')
    list_filter = ('sequencer', 'cluster_station', 'paired_end')
    fieldsets = (
        (None, {
            'fields': ('run_date',
                       ('flowcell_id', 'cluster_station', 'sequencer'),
                       ('read_length', 'control_lane', 'paired_end'),)
        }),
        ('Notes:', {'fields': ('notes',), }),
    )
    inlines = [
        LaneInline,
    ]

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(FlowCellOptions, self).formfield_for_dbfield(db_field,
                                                                   **kwargs)

        # Override field attributes
        if db_field.name == 'sequencer':
            # seems kind of clunky.
            # the goal is to replace the default select/combo box with one
            # that can strike out disabled options.
            attrs = field.widget.widget.attrs
            field.widget.widget = SequencerSelect(
                attrs=attrs,
                queryset=field.queryset)
        elif db_field.name == "notes":
            field.widget.attrs["rows"] = "3"
        return field


@admin.register(ClusterStation)
class ClusterStationOptions(admin.ModelAdmin):
    list_display = ('name', 'isdefault',)
    fieldsets = ((None, {'fields': ('name', 'isdefault')}),)


class SequencerSelect(Select):
    def __init__(self, queryset=None, *args, **kwargs):
        super(SequencerSelect, self).__init__(*args, **kwargs)
        self.queryset = queryset

    def render_option(self, selected_choices, option_value, option_label):
        disabled_sequencers = [str(s.id) for s in
                               self.queryset.filter(active=False)]
        option_value = str(option_value)
        selected_html = (option_value in selected_choices) and \
                        u' selected="selected"' or ''
        cssclass = "strikeout" if option_value in disabled_sequencers else ''
        return u'<option class="%s" value="%s"%s>%s</option>' % (
            cssclass, escape(option_value), selected_html,
            conditional_escape(force_str(option_label)))


@admin.register(Sequencer)
class SequencerOptions(admin.ModelAdmin):
    list_display = ('name', 'active', 'isdefault', 'instrument_name', 'model')
    fieldsets = ((None,
                  {'fields': (
                      'name',
                      ('active', 'isdefault'),
                      'instrument_name',
                      'serial_number',
                      'model', 'comment')}), )
