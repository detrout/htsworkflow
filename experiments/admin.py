from __future__ import absolute_import, print_function, unicode_literals

from itertools import chain

from django.contrib import admin
from django.forms import ModelForm
from django.forms.fields import CharField
from django.forms.widgets import TextInput, Select
from django.utils.encoding import force_text
from django.utils.html import escape, conditional_escape

from .models import (
    FlowCell,
    DataRun,
    DataFile,
    FileType,
    ClusterStation,
    Sequencer,
    Lane
)


class DataFileForm(ModelForm):
    class Meta:
        model = DataFile
        fields = ('random_key', 'data_run', 'library',
                  'file_type', 'relative_pathname')


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
admin.site.register(DataRun, DataRunOptions)


class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'mimetype', 'regex')
admin.site.register(FileType, FileTypeAdmin)


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
admin.site.register(Lane, LaneOptions)


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
admin.site.register(FlowCell, FlowCellOptions)


class ClusterStationOptions(admin.ModelAdmin):
    list_display = ('name', 'isdefault',)
    fieldsets = ((None, {'fields': ('name', 'isdefault')}),)
admin.site.register(ClusterStation, ClusterStationOptions)


class SequencerSelect(Select):
    def __init__(self, queryset=None, *args, **kwargs):
        super(SequencerSelect, self).__init__(*args, **kwargs)
        self.queryset = queryset

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set([force_text(v) for v in selected_choices])
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' %
                              escape(force_text(option_value)))
                for option in option_label:
                    output.append(
                        self.render_option(selected_choices,
                                           *option))
                output.append(u'</optgroup>')
            else:
                output.append(
                    self.render_option(selected_choices,
                                       option_value,
                                       option_label))
        return u'\n'.join(output)

    def render_option(self, selected_choices, option_value, option_label):
        disabled_sequencers = [str(s.id) for s in
                               self.queryset.filter(active=False)]
        option_value = str(option_value)
        selected_html = (option_value in selected_choices) and \
                        u' selected="selected"' or ''
        cssclass = "strikeout" if option_value in disabled_sequencers else ''
        return u'<option class="%s" value="%s"%s>%s</option>' % (
            cssclass, escape(option_value), selected_html,
            conditional_escape(force_text(option_label)))


class SequencerOptions(admin.ModelAdmin):
    list_display = ('name', 'active', 'isdefault', 'instrument_name', 'model')
    fieldsets = ((None,
                  {'fields': (
                      'name',
                      ('active', 'isdefault'),
                      'instrument_name',
                      'serial_number',
                      'model', 'comment')}), )

admin.site.register(Sequencer, SequencerOptions)
