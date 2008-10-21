from django.conf.urls.defaults import *

urlpatterns = patterns('',                                               
    (r'^updStatus$', 'htswfrontend.analys_track.main.updStatus'),
    (r'^getProjects/$', 'htswfrontend.analys_track.main.getProjects'),
)
