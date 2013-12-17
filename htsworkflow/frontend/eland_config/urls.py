from django.conf.urls import patterns, url

urlpatterns = patterns('',
    ## Example:

    url(r'^(?P<flowcell>\w+)/$', 'htsworkflow.frontend.eland_config.views.config'),
    url(r'^$', 'htsworkflow.frontend.eland_config.views.config'),
    #url(r'^$', 'htsworkflow.frontend.eland_config.views.index')

)
