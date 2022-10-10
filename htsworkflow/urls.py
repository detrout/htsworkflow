from django.urls import include, path
from django.contrib import admin
admin.autodiscover()


from experiments.views import (
    FlowCellListView,
    flowcell_lane_detail,
    flowcell_detail,
    lanes_for,
    sequencer,
)
from samples.views import library_id_to_admin_url

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    # Base:
    path("eland_config/", include("eland_config.urls")),
    # Experiments:
    path("experiments/", include("experiments.urls")),
    path("lane/<lane_pk>", flowcell_lane_detail, name="flowcell_lane_detail"),
    path("flowcell/<flowcell_id>/", flowcell_detail, name="flowcell_detail"),
    path(
        "flowcell/<flowcell_id>/<lane_number>/",
        flowcell_detail,
        name="flowcell_detail",
    ),
    path("flowcell/", FlowCellListView.as_view(), name="flowcell_index"),
    path("inventory/", include("inventory.urls")),
    path("library/", include("samples.urls")),
    path("lanes_for/", lanes_for, name="lanes_for"),
    path("lanes_for/<username>", lanes_for, name="lanes_for"),
    ### library id to admin url
    path("library_id_to_admin_url/<library_id>/", library_id_to_admin_url),
    path("sequencer/<sequencer_id>", sequencer, name="sequencer"),
    path("admin/", admin.site.urls),
]
