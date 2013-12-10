from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'htsworkflow.frontend.experiments.views.index'),
    #(r'^liblist$', 'htsworkflow.frontend.experiments.views.test_Libs'),
    #(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.experiments.views.detail'),
    (r'^config/(?P<fc_id>.+)/json$', 'htsworkflow.frontend.experiments.experiments.flowcell_json'),
    (r'^lanes_for/(?P<username>.+)/json$', 'htsworkflow.frontend.experiments.experiments.lanes_for_json'),
    (r'^file/(?P<key>.+)/?$', 'htsworkflow.frontend.experiments.views.read_result_file'),
    (r'^started/(?P<pk>.+)/$', 'htsworkflow.frontend.experiments.views.startedEmail'),
    (r'^finished/(?P<pk>.+)/$', 'htsworkflow.frontend.experiments.views.finishedEmail'),
                        
)
