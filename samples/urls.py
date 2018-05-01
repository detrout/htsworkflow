from __future__ import unicode_literals

from django.conf.urls import url

from samples.views import (
    library,
    library_not_run,
    library_to_flowcells,
    library_json,
    species_json,
    species,
    antibodies,
)

urlpatterns = [
    # View livrary list
    url(r'^$', library),
    url(r'^not_run/$', library_not_run),
    url(r'^(?P<lib_id>\w+)/$', library_to_flowcells, name='library_to_flowcells'),
    url(r"^species/(?P<species_id>\w+)/json$", species_json),
    url(r"^(?P<library_id>\w+)/json$", library_json, name='library_json'),
    url(r"^species/(?P<species_id>\w+)$", species, name='species'),
    url(r"^antibody/$", antibodies),
]
