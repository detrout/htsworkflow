import os
from .base import *

ALLOWED_HOSTS = ['jumpgate.caltech.edu']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'fctracker.db'),
    }
}
