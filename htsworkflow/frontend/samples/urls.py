from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r"^library/(?P<library_id>\w+)/json", 'htsworkflow.frontend.samples.views.library_json'),
    url(r"^species/(?P<species_id>\w+)/json", 'htsworkflow.frontend.samples.views.species_json'),
    url(r"^species/(?P<species_id>\w+)", 'htsworkflow.frontend.samples.views.species'),
    url(r"^antibody/$", 'htsworkflow.frontend.samples.views.antibodies'),
)
