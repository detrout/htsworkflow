from django.conf.urls.defaults import *

# Databrowser:
from django.contrib import databrowse
from fctracker.models import Library, FlowCell
databrowse.site.register(Library)
databrowse.site.register(FlowCell)

urlpatterns = patterns('',
    # Base:
    (r'^elandifier/', include('elandifier.eland_config.urls')),
    # Admin:
     (r'^admin/', include('django.contrib.admin.urls')),
    # Databrowser:
     (r'^databrowse/(.*)', databrowse.site.root),
)
