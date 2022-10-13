from __future__ import unicode_literals
from django.urls import path

from bcmagic.views import (
    json_test,
    magic,
    index,
)

urlpatterns = [
    path("", index, name="bcmagic_index"),
    path("json_test/", json_test, name="bcmagic_json_test"),
    path("magic/", magic, name="bcmagic_index"),
]
