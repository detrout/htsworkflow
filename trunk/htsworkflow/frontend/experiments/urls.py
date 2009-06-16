from django.conf.urls.defaults import *

urlpatterns = patterns('',
                                                                                                      
    (r'^$', 'htsworkflow.frontend.experiments.views.index'),
    #(r'^liblist$', 'htsworkflow.frontend.experiments.views.test_Libs'),
    #(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.experiments.views.detail'),
    (r'^(?P<fcid>.+)/$', 'htsworkflow.frontend.experiments.views.makeFCSheet'),
    (r'^updStatus$', 'htsworkflow.frontend.experiments.experiments.updStatus'),
    (r'^getConfile$', 'htsworkflow.frontend.experiments.experiments.getConfile'),
    (r'^getLanesNames$', 'htsworkflow.frontend.experiments.experiments.getLaneLibs')   
)
