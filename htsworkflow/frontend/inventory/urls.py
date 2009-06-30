from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # DATA
     (r'^data/items/$', 'htsworkflow.frontend.inventory.views.data_items'),
    # REMOTE LINKING
     (r'^lts/link/(?P<flowcell>.+)/(?P<serial>.+)/$', 'htsworkflow.frontend.inventory.views.link_flowcell_and_device'),
     
    # INDEX
     (r'^$', 'htsworkflow.frontend.inventory.views.index')
    )
