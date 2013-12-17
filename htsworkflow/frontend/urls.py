from django.conf.urls import include, patterns, url
from django.contrib import admin
import django
admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    url('^accounts/login/$', 'django.contrib.auth.views.login'),
    url('^accounts/logout/$', 'django.contrib.auth.views.logout'),
    url('^accounts/logout_then_login/$', 'django.contrib.auth.views.logout_then_login'),
    url('^accounts/password_change/$', 'django.contrib.auth.views.password_change'),
    url('^accounts/password_change_done/$', 'django.contrib.auth.views.password_change_done'),
    #url('^accounts/profile/$', 'htsworkflow.frontend.samples.views.user_profile'),
    # Base:
    url(r'^eland_config/', include('htsworkflow.frontend.eland_config.urls')),
    ### MOVED Admin from here ###
    # Experiments:
    url(r'^experiments/', include('htsworkflow.frontend.experiments.urls')),
    ### Flowcell:
    url(r'^lane/(?P<lane_pk>\w+)',
        'htsworkflow.frontend.experiments.views.flowcell_lane_detail'),
    url(r'^flowcell/(?P<flowcell_id>\w+)/((?P<lane_number>\w+)/)?$',
        'htsworkflow.frontend.experiments.views.flowcell_detail'),
    ## AnalysTrack:
    ##(r'^analysis/', include('htsworkflow.frontend.analysis.urls')),
    ## Inventory urls
    url(r'^inventory/', include('htsworkflow.frontend.inventory.urls')),
    ## Report Views:
    ##url(r'^reports/', include('htsworkflow.frontend.reports.urls')),
    ## Library browser
    url(r'^library/$', 'htsworkflow.frontend.samples.views.library'),
    url(r'^library/not_run/$',
        'htsworkflow.frontend.samples.views.library_not_run'),
    url(r'^library/(?P<lib_id>\w+)/$',
        'htsworkflow.frontend.samples.views.library_to_flowcells'),
    url(r'^lanes_for/$', 'htsworkflow.frontend.samples.views.lanes_for'),
    url(r'^lanes_for/(?P<username>\w+)', 'htsworkflow.frontend.samples.views.lanes_for'),
    ### library id to admin url
    url(r'^library_id_to_admin_url/(?P<lib_id>\w+)/$',
        'htsworkflow.frontend.samples.views.library_id_to_admin_url'),
    ### sample / library information
    url(r'^samples/', include('htsworkflow.frontend.samples.urls')),
    url(r'^sequencer/(?P<sequencer_id>\w+)',
        'htsworkflow.frontend.experiments.views.sequencer'),
    ## Raw result files
    #url(r'^results/(?P<flowcell_id>\w+)/(?P<cnm>C[0-9]+-[0-9]+)/summary/',
      #'htsworkflow.frontend.samples.views.summaryhtm_fc_cnm'),
    #url(r'^results/(?P<flowcell_id>\w+)/(?P<cnm>C[0-9]+-[0-9]+)/eland_result/(?P<lane>[1-8])',
      #'htsworkflow.frontend.samples.views.result_fc_cnm_eland_lane'),
    #url(r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])/ucsc',
      #'htsworkflow.frontend.samples.views.bedfile_fc_cnm_eland_lane_ucsc'),
    #url(r'^results/(?P<fc_id>\w+)/(?P<cnm>C[1-9]-[0-9]+)/bedfile/(?P<lane>[1-8])',
      #'htsworkflow.frontend.samples.views.bedfile_fc_cnm_eland_lane'),
    url(r'^bcmagic/', include('htsworkflow.frontend.bcmagic.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
  urlpatterns += patterns('',
      url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
  )
