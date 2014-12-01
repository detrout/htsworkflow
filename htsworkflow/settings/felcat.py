# configure debugging
import os
from .local import *

DEBUG=True
TEMPLATE_DEBUG = True

INTERNAL_IPS = ('127.0.0.1',)

MIDDLEWARE_CLASSES.extend([
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
])

DATABASES = {
    'fctracker': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/htsworkflow/htsworkflow/fctracker.db',
    },
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'felcat.caltech.edu',
        'USER': 'jumpgate',
        'NAME': 'htsworkflow',
    }

}

