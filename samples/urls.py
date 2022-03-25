from __future__ import unicode_literals

from django.conf.urls import url

from samples.views import (
    library,
    library_not_run,
    library_detail,
    library_json,
    species_json,
    species,
    antibodies,
)

urlpatterns = [
    # View library list
    url(r'^$', library, name='library_index'),
    url(r'^not_run/$', library_not_run, name='library_not_run'),
    url(r'^(?P<lib_id>\w+)/$', library_detail, name='library_detail'),
    url(r"^(?P<library_id>\w+)/json$", library_json, name='library_json'),
    url(r"^species/(?P<species_id>\w+)/json$", species_json, name='species_json'),
    url(r"^species/(?P<species_id>\w+)$", species, name='species'),
    url(r"^antibody/$", antibodies, name='antibodies'),
]
