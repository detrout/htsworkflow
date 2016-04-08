from __future__ import unicode_literals

from django.conf.urls import url

from .views import (
    data_items,
    link_flowcell_and_device,
    itemtype_index,
    item_summary_by_uuid,
    item_print,
    item_summary_by_barcode,
    all_index,
    index

)
urlpatterns = [
    # DATA
    url(r'^data/items/$', data_items),
    # REMOTE LINKING
    url(r'^lts/link/(?P<flowcell>.+)/(?P<serial>.+)/$', link_flowcell_and_device),

    # INDEX
    url(r'^it/(?P<name>.+)/$', itemtype_index),
    url(r'^(?P<uuid>[a-fA-F0-9]{32})/$', item_summary_by_uuid),
    url(r'^(?P<uuid>[a-fA-F0-9]{32})/print/$', item_print),
    url(r'^(?P<barcode_id>.+)/$', item_summary_by_barcode),
    url(r'^all_index/$', all_index),
    url(r'^$', index)
]
