from django.contrib import admin
from htsworkflow.frontend.bcmagic.models import KeywordMap

class KeywordMapAdmin(admin.ModelAdmin):
    list_display = ('keyword','regex', 'url_template')

admin.site.register(KeywordMap, KeywordMapAdmin)