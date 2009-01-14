from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

# Databrowser:
#from django.contrib import databrowse
#from htsworkflow.frontend.samples.models import Library
#databrowse.site.register(Library)
#databrowse.site.register(FlowCell)

urlpatterns = patterns('',
    # Base:
    (r'^eland_config/', include('htsworkflow.frontend.eland_config.urls')),
    # Admin:
    (r'^admin/(.*)', admin.site.root),
    # Experiments:
    (r'^experiments/', include('htsworkflow.frontend.experiments.urls')),
    # AnalysTrack:
    #(r'^analysis/', include('htsworkflow.frontend.analysis.urls')),
    # Report Views:
    # (r'^reports/', include('gaworkflow.frontend....urls')),
    
    # databrowser
    #(r'^databrowse/(.*)', databrowse.site.root)
)
