from __future__ import unicode_literals

from django.conf.urls import patterns, url

urlpatterns = patterns('',
    ## Example:

    url(r'^(?P<flowcell>\w+)/$', 'eland_config.views.config'),
    url(r'^$', 'eland_config.views.config'),
    #url(r'^$', 'htsworkflow.frontend.eland_config.views.index')

)
