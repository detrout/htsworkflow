from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^json_test/$', 'bcmagic.views.json_test'),
    (r'^magic/$', 'bcmagic.views.magic'),
    (r'^$', 'bcmagic.views.index'),
)
