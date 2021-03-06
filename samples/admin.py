from __future__ import absolute_import, print_function, unicode_literals

from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.template import Context, Template

from .models import (
    AccessionAgency,
    LibraryAccession,
    Antibody,
    Cellline,
    Condition,
    ExperimentType,
    HTSUser,
    LibraryType,
    MultiplexIndex,
    Species,
    Affiliation,
    Library
)
from experiments.models import Lane
from inventory.models import PrinterTemplate
from bcmagic.utils import print_zpl_socket

# Let's disable those pesky delete everything by accident features.
admin.site.disable_action('delete_selected')


class AccessionAgencyOptions(admin.ModelAdmin):
    model = AccessionAgency


class LibraryAccessionOptions(admin.ModelAdmin):
    model = LibraryAccession
    search_fields = ('accession', 'library')
    list_filter = ('agency', 'created',)
    list_display = ('accession', 'library', 'created')


class LibraryAccessionInline(admin.TabularInline):
    model = LibraryAccession
    fieldsets = (
        (None, {
            'fields': ('agency', 'accession', 'url')
        }),
    )


class AffiliationOptions(admin.ModelAdmin):
    list_display = ('name', 'contact', 'email')
    fieldsets = (
        (None, {
            'fields': (('name', 'contact', 'email', 'users'))
        }),
    )

    # some post 1.0.2 version of django has formfield_overrides
    # which would replace this code with:
    # formfield_overrids = {
    #   models.ManyToMany: { 'widget': widgets.FilteredSelectMultiple }
    # }
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'users':
            kwargs['widget'] = widgets.FilteredSelectMultiple(
                db_field.verbose_name,
                (db_field.name in self.filter_vertical))
        rv = super(AffiliationOptions, self).formfield_for_dbfield(
            db_field,
            **kwargs)
        #  print db_field.name, kwargs
        return rv


class AntibodyOptions(admin.ModelAdmin):
    search_fields = ('antigene', 'nickname', 'catalog',
                     'antibodies', 'source', 'biology', 'notes')
    list_display = ('antigene', 'nickname', 'antibodies',
                    'catalog', 'source', 'biology', 'notes')
    list_filter = ('antibodies', 'source')
    fieldsets = (
        (None, {
            'fields': (('antigene', 'nickname', 'antibodies'),
                       ('catalog', 'source'),
                       ('biology'),
                       ('notes'))
        }),
    )


class CelllineOptions(admin.ModelAdmin):
    list_display = ('cellline_name', 'notes')
    search_fields = ('cellline_name', 'nickname', 'notes')
    fieldsets = (
        (None, {
            'fields': (('cellline_name', 'nickname',),
                       ('notes'),)
        }),
    )


class ConditionOptions(admin.ModelAdmin):
    list_display = (('condition_name'), ('notes'),)
    fieldsets = (
        (None, {
            'fields': (('condition_name'),
                       ('nickname'),
                       ('notes'),)
        }),
    )


class ExperimentTypeOptions(admin.ModelAdmin):
    model = ExperimentType
    list_display = ('name',)
    fieldsets = ((None, {'fields': ('name',)}),)


class HTSUserCreationForm(UserCreationForm):
    class Meta:
        model = HTSUser
        fields = ('username', 'first_name', 'last_name')


class HTSUserChangeForm(UserChangeForm):
    class Meta:
        model = HTSUser
        fields = ('username', 'first_name', 'last_name')


class HTSUserOptions(UserAdmin):
    form = HTSUserChangeForm
    add_form = HTSUserCreationForm


class LaneLibraryInline(admin.StackedInline):
    model = Lane
    extra = 0


class Library_Inline(admin.TabularInline):
    model = Library


class LibraryTypeOptions(admin.ModelAdmin):
    list_display = ['name', 'is_paired_end', 'can_multiplex']
    model = LibraryType


class MultiplexIndexOptions(admin.ModelAdmin):
    model = MultiplexIndex
    list_display = ['adapter_type', 'multiplex_id', 'sequence']


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
        'libraryaccession__accession',
    )
    list_display = (
        'id',
        'library_name',
        'index_sequence_text',
        'affiliation',
        'undiluted_concentration',
        'gel_cut_size',
        'creation_date',
    )
    list_filter = (
        'hidden',
        'experiment_type',
        'library_type',
        # 'cell_line',
        'stopping_point',
        'made_by',
        'library_species',
        'affiliations',
        )
    list_display_links = ('id', 'library_name',)
    fieldsets = (
        (None, {
            'fields': (
                ('id', 'library_name', 'hidden'),
                ('library_species', 'experiment_type'),
                ('library_type', 'multiplex_id'),
            )
        }),
        ('Experiment Detail:', {
            'fields': (
                ('cell_line', 'replicate',),
                ('condition',),
                ('antibody', )
            ),
            'classes': ('collapse',),
        }),
        ('Creation Information:', {
            'fields': (
                ('made_by', 'creation_date', 'stopping_point'),
                ('amplified_from_sample'),
                ('gel_cut_size', 'insert_size', 'undiluted_concentration'),
                ('bioanalyzer_concentration', 'bioanalyzer_image_url'),
                ('bioanalyzer_summary'),
                ('notes'))
        }),
        ('Library/Project Affiliation:', {
            'fields': (('account_number', 'affiliations'),)
        }),
    )
    inlines = [
        LaneLibraryInline,
        LibraryAccessionInline,
    ]
    actions = ['action_print_library_labels']

    def action_print_library_labels(self, request, queryset):
        """Django action which prints labels for the selected set of labels from the
        Django Admin interface.
        """

        # Probably should ask if the user really meant to print all selected
        # libraries if the count is above X. X=10 maybe?

        # Grab the library template
        # FIXME: Hardcoding library template name. Not a good idea... *sigh*.
        EVIL_HARDCODED_LIBRARY_TEMPLATE_NAME = "Library"

        try:
            template = PrinterTemplate.objects.get(
                item_type__name=EVIL_HARDCODED_LIBRARY_TEMPLATE_NAME)
        except PrinterTemplate.DoesNotExist:
            self.message_user(
                request,
                "Could not find a library template with ItemType.name of '%s'" %
                (EVIL_HARDCODED_LIBRARY_TEMPLATE_NAME))
            return

        # ZPL Template
        t = Template(template.template)

        zpl_list = []
        # Iterate over selected labels to print
        for library in queryset.all():

            # Django Template Context
            c = Context({'library': library})

            # Send rendered template to the printer that the template
            #  object has been attached to in the database.
            zpl_list.append(t.render(c))

        print_zpl_socket(zpl_list, host=template.printer.ip_address)

        self.message_user(request, "%s labels printed." % (len(queryset)))

    action_print_library_labels.short_description = "Print Labels"

    def formfield_for_dbfield(self, db_field, **kwargs):
        # Override Field type
        if db_field.name in ('affiliations', 'tags'):
            kwargs['widget'] = widgets.FilteredSelectMultiple(
                db_field.verbose_name,
                (db_field.name in self.filter_vertical)
            )
        field = super(LibraryOptions, self).formfield_for_dbfield(db_field,
                                                                  **kwargs)
        # Override field attributes
        if db_field.name == "bioanalyzer_summary":
            field.widget.attrs["rows"] = "3"
        return field


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

admin.site.register(AccessionAgency, AccessionAgencyOptions)
admin.site.register(LibraryAccession, LibraryAccessionOptions)
admin.site.register(Library, LibraryOptions)
admin.site.register(Affiliation, AffiliationOptions)
admin.site.register(Antibody, AntibodyOptions)
admin.site.register(Cellline, CelllineOptions)
admin.site.register(Condition, ConditionOptions)
admin.site.register(ExperimentType, ExperimentTypeOptions)
admin.site.register(LibraryType, LibraryTypeOptions)
admin.site.register(MultiplexIndex, MultiplexIndexOptions)
admin.site.register(Species, SpeciesOptions)
