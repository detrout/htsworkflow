from __future__ import unicode_literals

from django.contrib import admin
from .models import KeywordMap, Printer


class KeywordMapAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'regex', 'url_template')


class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'ip_address', 'label_shape',
                    'label_width', 'label_height', 'notes')


admin.site.register(KeywordMap, KeywordMapAdmin)
admin.site.register(Printer, PrinterAdmin)
