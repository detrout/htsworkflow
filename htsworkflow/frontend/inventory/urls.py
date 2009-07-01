from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # DATA
     (r'^data/items/$', 'htsworkflow.frontend.inventory.views.data_items'),
    # REMOTE LINKING
     (r'^lts/link/(?P<flowcell>.+)/(?P<serial>.+)/$', 'htsworkflow.frontend.inventory.views.link_flowcell_and_device'),
     
    # INDEX
    (r'^(?P<uuid>[a-fA-F0-9]{32})/$', 'htsworkflow.frontend.inventory.views.item_summary'),
     (r'^$', 'htsworkflow.frontend.inventory.views.index')
    )
