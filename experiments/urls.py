from __future__ import unicode_literals

from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'experiments.views.index'),
    #(r'^liblist$', 'htsworkflow.frontend.experiments.views.test_Libs'),
    #(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.experiments.views.detail'),
    (r'^config/(?P<fc_id>.+)/json$', 'experiments.experiments.flowcell_json'),
    (r'^lanes_for/(?P<username>.+)/json$', 'experiments.experiments.lanes_for_json'),
    (r'^file/(?P<key>.+)/?$', 'experiments.views.read_result_file'),
    (r'^started/(?P<pk>.+)/$', 'experiments.views.startedEmail'),
    (r'^finished/(?P<pk>.+)/$', 'experiments.views.finishedEmail'),
)
