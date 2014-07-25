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
    #'default': {
        #'ENGINE': 'django.db.backends.sqlite3',
        #'NAME': os.path.join(settings.BASE_DIR, '..', 'fctracker.db'),
    #}
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'felcat.caltech.edu',
        'USER': 'diane',
        'NAME': 'htsworkflow-django1.7',
    }

}

