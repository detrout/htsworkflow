from django.conf.urls.defaults import *

urlpatterns = patterns('',                                               
    (r'^updLibInfo$', 'htsworkflow.reports.libinfopar.refreshLibInfoFile'),
    (r'^report$', 'htsworkflow.reports.reports.report1'),
    (r'^report_RM$', 'htsworkflow.reports.reports.report_RM'),
    (r'^report_FCs$', 'htsworkflow.reports.reports.getNotRanFCs'),
    (r'^liblist$', 'htsworkflow.reports.reports.test_Libs')
)
