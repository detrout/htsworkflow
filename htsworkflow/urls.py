from django.conf.urls import include, patterns, url
from django.contrib import admin
import django
admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    url('^accounts/', include('django.contrib.auth.urls')),
    # Base:
    url(r'^eland_config/', include('eland_config.urls')),
    # Experiments:
    url(r'^experiments/', include('experiments.urls')),
    url(r'^lane/(?P<lane_pk>\w+)',
        'experiments.views.flowcell_lane_detail'),
    url(r'^flowcell/(?P<flowcell_id>\w+)/((?P<lane_number>\w+)/)?$',
        'experiments.views.flowcell_detail'),
    url(r'^inventory/', include('inventory.urls')),
    url(r'^library/', include('samples.urls')),
    url(r'^lanes_for/$', 'experiments.views.lanes_for'),
    url(r'^lanes_for/(?P<username>[-_ \w]+)', 'experiments.views.lanes_for'),
    ### library id to admin url
    url(r'^library_id_to_admin_url/(?P<lib_id>\w+)/$',
        'samples.views.library_id_to_admin_url'),
    ### sample / library information
    url(r'^samples/', include('samples.urls')),
    url(r'^sequencer/(?P<sequencer_id>\w+)',
        'experiments.views.sequencer'),

    url(r'^admin/', include(admin.site.urls)),
)
