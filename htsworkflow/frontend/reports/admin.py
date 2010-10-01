from htsworkflow.frontend.reports.models import ProgressReport
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class ProgressReportOptions(admin.ModelAdmin):
  list_display = ('Study','ab_batch','cell_line','library','sequencing','aligned_reads','QPCR','submit_to_DCC','submit_to_NCBI','interactome_complete')
  ## list_filter = ('interactome_complete')

#admin.site.register(ProgressReport, ProgressReportOptions)

