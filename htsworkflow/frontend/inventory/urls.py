from django.conf.urls import patterns

urlpatterns = patterns('',
    # DATA
     (r'^data/items/$', 'htsworkflow.frontend.inventory.views.data_items'),
    # REMOTE LINKING
     (r'^lts/link/(?P<flowcell>.+)/(?P<serial>.+)/$', 'htsworkflow.frontend.inventory.views.link_flowcell_and_device'),

    # INDEX
    (r'^it/(?P<name>.+)/$', 'htsworkflow.frontend.inventory.views.itemtype_index'),
    (r'^(?P<uuid>[a-fA-F0-9]{32})/$', 'htsworkflow.frontend.inventory.views.item_summary_by_uuid'),
    (r'^(?P<uuid>[a-fA-F0-9]{32})/print/$', 'htsworkflow.frontend.inventory.views.item_print'),
    (r'^(?P<barcode_id>.+)/$', 'htsworkflow.frontend.inventory.views.item_summary_by_barcode'),
    (r'^all_index/$', 'htsworkflow.frontend.inventory.views.all_index'),
    (r'^$', 'htsworkflow.frontend.inventory.views.index')
    )
