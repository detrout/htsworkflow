from django.conf.urls.defaults import *

urlpatterns = patterns('',                                               
    (r'^updLibInfo$', 'htsworkflow.reports.libinfopar.refreshLibInfoFile'),
)
