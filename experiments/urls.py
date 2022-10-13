from __future__ import unicode_literals

from django.urls import path

from .experiments import flowcell_json, lanes_for_json
from .views import (
    index,
    read_result_file,
    startedEmail,
    finishedEmail,
)

urlpatterns = [
    path("", index, name="flowcell_index"),
    # url(r'^liblist$', 'htsworkflow.frontend.experiments.views.test_Libs'),
    # url(r'^(?P<run_folder>.+)/$', 'gaworkflow.frontend.experiments.views.detail'),
    path("config/<fc_id>/json", flowcell_json, name="flowcell_config_json"),
    path("lanes_for/<username>/json", lanes_for_json, name="lanes_for_json"),
    path("file/<key>", read_result_file, name="read_result_file"),
    path("started/<pk>/", startedEmail, name="started_email"),
    path("finished/<pk>", finishedEmail, name="finished_email"),
]
