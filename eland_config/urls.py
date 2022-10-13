from __future__ import unicode_literals

from django.urls import path

from .views import config

urlpatterns = [
    path("<flowcell>/", config),
    path("", config),
]
