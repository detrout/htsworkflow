from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    
    (r'^(?P<flowcell>\w+)/$', 'htsworkflow.frontend.eland_config.views.config'),
    (r'^$', 'htsworkflow.frontend.eland_config.views.config'),
    #(r'^$', 'htsworkflow.frontend.eland_config.views.index')

)
