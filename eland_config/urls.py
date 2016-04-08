from __future__ import unicode_literals

from django.conf.urls import url

from .views import config

urlpatterns = [
    url(r'^(?P<flowcell>\w+)/$', config),
    url(r'^$', config),
]
