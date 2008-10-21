from django.conf.urls.defaults import *

# Databrowser:
from django.contrib import databrowse
from fctracker.models import Library, FlowCell
databrowse.site.register(Library)
databrowse.site.register(FlowCell)

urlpatterns = patterns('',
    # Base:
    (r'^eland_config/', include('htsworkflow.frontend.eland_config.urls')),
    # Admin:
     (r'^admin/', include('django.contrib.admin.urls')),
    # ExpTrack:
     (r'^experiments/', include('htswfrontend.experiments.et_urls')),
    # AnalysTrack:
     (r'^analysis/', include('htswfrontend.analysis.an_urls')),
    # Report Views:
    # (r'^reports/', include('gaworkflow.frontend....urls')),
)
