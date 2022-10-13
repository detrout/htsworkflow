from __future__ import unicode_literals

from django.urls import path, re_path

from .views import (
    data_items,
    link_flowcell_and_device,
    itemtype_index,
    item_summary_by_uuid,
    item_print,
    item_summary_by_barcode,
    all_index,
    index,
)

urlpatterns = [
    # DATA
    path("data/items/", data_items),
    # REMOTE LINKING
    path(
        r"lts/link/<flowcell>/<serial>)/",
        link_flowcell_and_device,
        name="link_flowcell_and_device",
    ),
    # INDEX
    path("it/<name>", itemtype_index, name="itemtype_index"),
    re_path(
        r"^(?P<uuid>[a-fA-F0-9]{32})/$",
        item_summary_by_uuid,
        name="item_summary_by_uuid",
    ),
    re_path("^(?P<uuid>[a-fA-F0-9]{32})/print/$", item_print),
    path("<barcode_id>/", item_summary_by_barcode),
    path("all_index/", all_index),
    path("", index, name="inventory_index"),
]
