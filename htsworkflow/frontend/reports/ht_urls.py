from django.conf.urls.defaults import *

urlpatterns = patterns('',                                               
    (r'^updLibInfo$', 'htswfrontend.htsw_reports.libinfopar.refreshLibInfoFile'),
)
