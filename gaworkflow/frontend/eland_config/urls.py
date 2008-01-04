from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    
    (r'^(?P<flowcell>\w+)/$', 'gaworkflow.frontend.eland_config.views.config'),
    (r'^$', 'gaworkflow.frontend.eland_config.views.config'),
    #(r'^$', 'gaworkflow.frontend.eland_config.views.index')

)
