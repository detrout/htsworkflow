from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r"^library/(?P<library_id>\w+)/json", 'htsworkflow.frontend.samples.views.library_json'),
    (r"^species/(?P<species_id>\w+)/json", 'htsworkflow.frontend.samples.views.species_json'),
    (r"^species/(?P<species_id>\w+)", 'htsworkflow.frontend.samples.views.species'),
    (r"^antibody/$", 'htsworkflow.frontend.samples.views.antibodies'),                   
)
