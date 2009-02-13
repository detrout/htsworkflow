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
    (r'^reports/', include('htsworkflow.frontend.reports.urls')),
    # Library browser
    (r'^library/$', 'htsworkflow.frontend.samples.views.library'),
    (r'^library/(?P<lib_id>\w+)/$', 
      'htsworkflow.frontend.samples.views.library_to_flowcells'),
    # Raw result files
    (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/summary/',
      'htsworkflow.frontend.samples.views.summaryhtm_fc_cnm'),
    (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/eland_result/(?P<lane>[1-8])',
      'htsworkflow.frontend.samples.views.result_fc_cnm_eland_lane'),
    (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])/ucsc',
      'htsworkflow.frontend.samples.views.bedfile_fc_cnm_eland_lane_ucsc'),
    (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])',
      'htsworkflow.frontend.samples.views.bedfile_fc_cnm_eland_lane'),
    
    # databrowser
    #(r'^databrowse/(.*)', databrowse.site.root)
)
