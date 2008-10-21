from django.conf.urls.defaults import *

urlpatterns = patterns('',
                                                                                                      
    (r'^$', 'htswfrontend.exp_track.views.index'),
    (r'^liblist$', 'htswfrontend.exp_track.views.test_Libs'),
    #(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.exp_track.views.detail'),
    (r'^(?P<fcid>.+)/$', 'htswfrontend.exp_track.views.makeFCSheet'),
    (r'^updStatus$', 'htswfrontend.exp_track.exptrack.updStatus'),
    (r'^getConfile$', 'htswfrontend.exp_track.exptrack.getConfile'),
    (r'^getLanesNames$', 'htswfrontend.exp_track.exptrack.getLaneLibs')   
)
