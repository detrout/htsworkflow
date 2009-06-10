from django.conf.urls.defaults import *

urlpatterns = patterns('',
     (r'^lts/link/(?P<flowcell>.+)/(?P<serial>.+)/$', 'htsworkflow.frontend.inventory.views.link_flowcell_and_device'),                                                                                                 
    )
