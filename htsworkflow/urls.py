from django.conf.urls import include,  url
from django.contrib import admin
admin.autodiscover()


from experiments.views import (
    flowcell_lane_detail,
    flowcell_detail,
    lanes_for,
    sequencer,
)
from samples.views import library_id_to_admin_url

urlpatterns = [
    url('^accounts/', include('django.contrib.auth.urls')),
    # Base:
    url(r'^eland_config/', include('eland_config.urls')),
    # Experiments:
    url(r'^experiments/', include('experiments.urls')),
    url(r'^lane/(?P<lane_pk>\w+)',
        flowcell_lane_detail, name="flowcell_lane_detail"),
    url(r'^flowcell/(?P<flowcell_id>\w+)/((?P<lane_number>\w+)/)?$',
        flowcell_detail, name="flowcell_detail"),
    url(r'^inventory/', include('inventory.urls')),
    url(r'^library/', include('samples.urls')),
    url(r'^lanes_for/(?P<username>[-_ \w]+)?',
        lanes_for, name='lanes_for'),
    ### library id to admin url
    url(r'^library_id_to_admin_url/(?P<lib_id>\w+)/$', library_id_to_admin_url),
    ### sample / library information
    url(r'^samples/', include('samples.urls')),
    url(r'^sequencer/(?P<sequencer_id>\w+)', sequencer, name="sequencer"),

    url(r'^admin/', admin.site.urls),
]
