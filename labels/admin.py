from __future__ import unicode_literals

from django.template import Context, Template
from django.contrib import admin

from .models import LabelContent, LabelTemplate, LabelPrinter
from inventory.models import PrinterTemplate
from bcmagic.utils import print_zpl_socket


class LabelContentOptions(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = (
        'title',
        'subtitle',
        'text',
        'barcode',
        'creator',
    )
    list_display = ('title', 'subtitle', 'text', 'barcode', 'template', 'creator')
    list_filter = ('template', 'creator',)
    fieldsets = (
        (None, {
            'fields': (('title', 'subtitle', 'text', 'barcode'),
                       ('template', 'creator'))

        }),
    )
    actions = ['action_print_labels']

    def action_print_labels(self, request, queryset):
        """
        Django action which prints labels for the selected set of labels from the
        Django Admin interface.
        """

        zpl_list = []
        #Iterate over selected labels to print
        for label in queryset.all():
            template_used = LabelTemplate.objects.get(name=label.template.name)
            # ZPL Template
            t = Template(template_used.ZPL_code)

            # Django Template Context
            c = Context({'label': label})

            # Send rendered template to the printer that the template
            #  object has been attached to in the database.
            zpl_list.append(t.render(c))

        print_zpl_socket(zpl_list, host=template_used.printer.ip_address)

        self.message_user(request, "%s labels printed." % (len(queryset)))

    action_print_labels.short_description = "Print Selected Labels"


class LabelTemplateOptions(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    list_display = ('name', 'printer', 'ZPL_code')


class LabelPrinterOptions(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'labels')

admin.site.register(LabelContent, LabelContentOptions)
admin.site.register(LabelTemplate, LabelTemplateOptions)
admin.site.register(LabelPrinter, LabelPrinterOptions)
