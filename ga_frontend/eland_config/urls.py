from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    
    (r'^config/(?P<flowcell>FC\d+)/$', 'ga_frontend.eland_config.views.config'),
    (r'^config/$', 'ga_frontend.eland_config.views.config'),
    (r'^$', 'ga_frontend.eland_config.views.index')

)
