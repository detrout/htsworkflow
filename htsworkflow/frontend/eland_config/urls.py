from django.conf.urls import patterns

urlpatterns = patterns('',
    # Example:
    
    (r'^(?P<flowcell>\w+)/$', 'htsworkflow.frontend.eland_config.views.config'),
    (r'^$', 'htsworkflow.frontend.eland_config.views.config'),
    #(r'^$', 'htsworkflow.frontend.eland_config.views.index')

)
