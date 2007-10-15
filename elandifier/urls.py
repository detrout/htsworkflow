from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    (r'^elandifier/', include('elandifier.eland_config.urls')),

    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
)
