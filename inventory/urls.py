from django.conf.urls import patterns

urlpatterns = patterns('',
    # DATA
     (r'^data/items/$', 'inventory.views.data_items'),
    # REMOTE LINKING
     (r'^lts/link/(?P<flowcell>.+)/(?P<serial>.+)/$', 'inventory.views.link_flowcell_and_device'),

    # INDEX
    (r'^it/(?P<name>.+)/$', 'inventory.views.itemtype_index'),
    (r'^(?P<uuid>[a-fA-F0-9]{32})/$', 'inventory.views.item_summary_by_uuid'),
    (r'^(?P<uuid>[a-fA-F0-9]{32})/print/$', 'inventory.views.item_print'),
    (r'^(?P<barcode_id>.+)/$', 'inventory.views.item_summary_by_barcode'),
    (r'^all_index/$', 'inventory.views.all_index'),
    (r'^$', 'inventory.views.index')
    )
