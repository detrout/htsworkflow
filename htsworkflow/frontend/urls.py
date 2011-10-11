from django.conf.urls.defaults import *
from django.contrib import admin
import django
admin.autodiscover()

# Databrowser:
#from django.contrib import databrowse
#from htsworkflow.frontend.samples.models import Library
#databrowse.site.register(Library)
#databrowse.site.register(FlowCell)

from django.conf import settings


urlpatterns = patterns('',
    ('^accounts/login/$', 'django.contrib.auth.views.login'),
    ('^accounts/logout/$', 'django.contrib.auth.views.logout'),
    ('^accounts/logout_then_login/$', 'django.contrib.auth.views.logout_then_login'),
    ('^accounts/password_change/$', 'django.contrib.auth.views.password_change'),
    ('^accounts/password_change_done/$', 'django.contrib.auth.views.password_change_done'),
    ('^accounts/profile/$', 'htsworkflow.frontend.samples.views.user_profile'),
    # Base:
    (r'^eland_config/', include('htsworkflow.frontend.eland_config.urls')),
    ### MOVED Admin from here ###
    #(r'^admin/(.*)', admin.site.root),
    # Experiments:
    (r'^experiments/', include('htsworkflow.frontend.experiments.urls')),
    # Flowcell:
    (r'^lane/(?P<lane_pk>\w+)',
     'htsworkflow.frontend.experiments.views.flowcell_lane_detail'),
    (r'^flowcell/(?P<flowcell_id>\w+)/((?P<lane_number>\w+)/)?$',
     'htsworkflow.frontend.experiments.views.flowcell_detail'),
    # AnalysTrack:
    #(r'^analysis/', include('htsworkflow.frontend.analysis.urls')),
    # Inventory urls
    (r'^inventory/', include('htsworkflow.frontend.inventory.urls')),
    # Report Views:
    (r'^reports/', include('htsworkflow.frontend.reports.urls')),
    # Library browser
    (r'^library/$', 'htsworkflow.frontend.samples.views.library'),
    (r'^library/not_run/$',
      'htsworkflow.frontend.samples.views.library_not_run'),
    (r'^library/(?P<lib_id>\w+)/$',
      'htsworkflow.frontend.samples.views.library_to_flowcells'),
    (r'^lanes_for/$', 'htsworkflow.frontend.samples.views.lanes_for'),
    (r'^lanes_for/(?P<username>\w+)', 'htsworkflow.frontend.samples.views.lanes_for'),
    # library id to admin url
    (r'^library_id_to_admin_url/(?P<lib_id>\w+)/$',
     'htsworkflow.frontend.samples.views.library_id_to_admin_url'),
    # sample / library information
    (r'^samples/', include('htsworkflow.frontend.samples.urls')),
    # Raw result files
    (r'^results/(?P<flowcell_id>\w+)/(?P<cnm>C[0-9]+-[0-9]+)/summary/',
      'htsworkflow.frontend.samples.views.summaryhtm_fc_cnm'),
    (r'^results/(?P<flowcell_id>\w+)/(?P<cnm>C[0-9]+-[0-9]+)/eland_result/(?P<lane>[1-8])',
      'htsworkflow.frontend.samples.views.result_fc_cnm_eland_lane'),
    (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])/ucsc',
      'htsworkflow.frontend.samples.views.bedfile_fc_cnm_eland_lane_ucsc'),
    (r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])',
      'htsworkflow.frontend.samples.views.bedfile_fc_cnm_eland_lane'),
    (r'^bcmagic/', include('htsworkflow.frontend.bcmagic.urls')),

    # databrowser
    #(r'^databrowse/(.*)', databrowse.site.root)
)

# Allow admin
if hasattr(admin.site, 'urls'):
  urlpatterns += patterns('', (r'^admin/', include(admin.site.urls)))
else:
  urlpatterns += patterns('', (r'^admin/(.*)', admin.site.root))

if settings.DEBUG:
  urlpatterns += patterns('',
      (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
  )
