from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^json_test/$', 'htsworkflow.frontend.bcmagic.views.json_test'),
    (r'^magic/$', 'htsworkflow.frontend.bcmagic.views.magic'),
    (r'^$', 'htsworkflow.frontend.bcmagic.views.index'),
)
