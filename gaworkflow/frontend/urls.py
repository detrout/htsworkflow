from django.conf.urls.defaults import *

# Databrowser:
from django.contrib import databrowse
from fctracker.models import Library, FlowCell
#databrowse.site.register(Library)
#databrowse.site.register(FlowCell)

urlpatterns = patterns('',
    # Base:
    (r'^eland_config/', include('gaworkflow.frontend.eland_config.urls')),
    # Admin:
     (r'^admin/', include('django.contrib.admin.urls')),
    # Databrowser:
     #(r'^databrowse/(.*)', databrowse.site.root),
     (r'^library/$', 'gaworkflow.frontend.fctracker.views.library'), 
     (r'^library/(?P<lib_id>\w+)/$', 'gaworkflow.frontend.fctracker.views.library_to_flowcells'),
     (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/summary/','gaworkflow.frontend.fctracker.views.summaryhtm_fc_cnm'),
     (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/eland_result/(?P<lane>[1-8])','gaworkflow.frontend.fctracker.views.result_fc_cnm_eland_lane'),
     (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])/ucsc','gaworkflow.frontend.fctracker.views.bedfile_fc_cnm_eland_lane_ucsc'),
     (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])','gaworkflow.frontend.fctracker.views.bedfile_fc_cnm_eland_lane'),
)
