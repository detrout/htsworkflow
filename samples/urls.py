from __future__ import unicode_literals

from django.urls import path

from samples.views import (
    library_index,
    library_not_run,
    library_detail,
    library_json,
    species_json,
    species,
    antibodies,
)

urlpatterns = [
    # View library list
    path("", library_index, name="library_index"),
    path("not_run/", library_not_run, name="library_not_run"),
    path("<library_id>/", library_detail, name="library_detail"),
    path("<library_id>/json", library_json, name="library_json"),
    path("species/<species_id>/json", species_json, name="species_json"),
    path("species/<species_id>", species, name="species"),
    path("antibody/", antibodies, name="antibodies"),
]
