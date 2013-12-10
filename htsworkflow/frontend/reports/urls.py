from django.conf.urls import patterns

urlpatterns = patterns('',                                               
    (r'^updLibInfo$', 'htsworkflow.frontend.reports.libinfopar.refreshLibInfoFile'),
    (r'^report$', 'htsworkflow.frontend.reports.reports.report1'),
    (r'^report_RM$', 'htsworkflow.frontend.reports.reports.report_RM'),
    (r'^report_FCs$', 'htsworkflow.frontend.reports.reports.getNotRanFCs'),
    (r'^liblist$', 'htsworkflow.frontend.reports.reports.test_Libs')
)
