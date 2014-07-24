from django.conf.urls import patterns, url

urlpatterns = patterns('samples.views',
    # View livrary list
    url(r'^$', 'library'),
    url(r'^not_run/$', 'library_not_run'),
    url(r'^(?P<lib_id>\w+)/$',
        'library_to_flowcells'),

    url(r"^library/(?P<library_id>\w+)/json$", 'library_json'),
    url(r"^species/(?P<species_id>\w+)/json$", 'species_json'),
    url(r"^species/(?P<species_id>\w+)$", 'species'),
    url(r"^antibody/$", 'antibodies'),
)
