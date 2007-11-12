from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    
    (r'^config/(?P<flowcell>FC\d+)/$', 'elandifier.eland_config.views.config'),
    (r'^config/$', 'elandifier.eland_config.views.config'),
    (r'^$', 'elandifier.eland_config.views.index')

)
