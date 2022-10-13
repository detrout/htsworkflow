# configure debugging
import os
from .local import *

DEBUG = True

INTERNAL_IPS = ('127.0.0.1',)
ALLOWED_HOSTS = ("localhost", "127.0.0.1", "::1")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(PROJECT_ROOT, "fctracker.db"),
    }
#    "default": {
#        "ENGINE": "django.db.backends.postgresql_psycopg2",
#        "HOST": "felcat.caltech.edu",
#        "USER": "diane",
#        "NAME": "htsworkflow-django1.11",
#    }
}
