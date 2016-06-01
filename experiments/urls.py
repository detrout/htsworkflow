from __future__ import unicode_literals

from django.conf.urls import url

from .experiments import flowcell_json, lanes_for_json
from .views import (index,
                    read_result_file,
                    startedEmail,
                    finishedEmail,
                    )

urlpatterns = [
    url(r'^$', index),
    #url(r'^liblist$', 'htsworkflow.frontend.experiments.views.test_Libs'),
    #url(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.experiments.views.detail'),
    url(r'^config/(?P<fc_id>.+)/json$', flowcell_json),
    url(r'^lanes_for/(?P<username>.+)/json$', lanes_for_json),
    url(r'^file/(?P<key>.+)/?$', read_result_file),
    url(r'^started/(?P<pk>.+)/$', startedEmail),
    url(r'^finished/(?P<pk>.+)/$', finishedEmail),
]
