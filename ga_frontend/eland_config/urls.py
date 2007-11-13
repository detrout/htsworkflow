from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    
    (r'^(?P<flowcell>FC\d+)/$', 'ga_frontend.eland_config.views.config'),
    (r'^$', 'ga_frontend.eland_config.views.config'),
    #(r'^$', 'ga_frontend.eland_config.views.index')

)
