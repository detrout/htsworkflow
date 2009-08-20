from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'htsworkflow.frontend.experiments.views.index'),
    #(r'^liblist$', 'htsworkflow.frontend.experiments.views.test_Libs'),
    #(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.experiments.views.detail'),
    (r'^fcsheet/(?P<fcid>.+)/$', 'htsworkflow.frontend.experiments.views.makeFCSheet'),
    (r'^updStatus$', 'htsworkflow.frontend.experiments.experiments.updStatus'),
    (r'^getConfile$', 'htsworkflow.frontend.experiments.experiments.getConfile'),
    (r'^getLanesNames$', 'htsworkflow.frontend.experiments.experiments.getLaneLibs'),
    # for the following two URLS I have to pass in the primary key
    # because I link to the page from an overridden version of the admin change_form
    # which only makes the object primary key available in the form.
    # (Or at least as far as I could tell)
    (r'^started/(?P<pk>.+)/$', 'htsworkflow.frontend.experiments.views.startedEmail'),
    (r'^finished/(?P<pk>.+)/$', 'htsworkflow.frontend.experiments.views.finishedEmail'),
)
