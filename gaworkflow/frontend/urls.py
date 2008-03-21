from django.conf.urls.defaults import *

# Databrowser:
from django.contrib import databrowse
from fctracker.models import Library, FlowCell
databrowse.site.register(Library)
databrowse.site.register(FlowCell)

urlpatterns = patterns('',
    # Base:
    (r'^eland_config/', include('gaworkflow.frontend.eland_config.urls')),
    # Admin:
     (r'^admin/', include('django.contrib.admin.urls')),
    # Databrowser:
     (r'^databrowse/(.*)', databrowse.site.root),
    # List of labs with read-only access:
     (r'^lab/$', 'gaworkflow.frontend.fctracker.views.labindex'),
    # Lab-specific access:
     (r'^lab/(\w+)/$', 'gaworkflow.frontend.fctracker.views.labdetail'),
)
