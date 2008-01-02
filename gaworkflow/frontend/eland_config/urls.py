from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    
    (r'^(?P<flowcell>[0-9a-zA-Z]+)/$', 'gaworkflow.frontend.eland_config.views.config'),
    (r'^$', 'gaworkflow.frontend.eland_config.views.config'),
    #(r'^$', 'gaworkflow.frontend.eland_config.views.index')

)
