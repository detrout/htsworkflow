from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^updStatus$', 'htsworkflow.frontend.analysis.main.updStatus'),
    (r'^getProjects/$', 'htsworkflow.frontend.analysis.main.getProjects'),
)
