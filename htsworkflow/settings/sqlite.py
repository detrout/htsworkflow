# -*- mode: python; coding: utf-8; python-indent-offset: 4; -*-

from .base import *

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(module)s %(levelname)s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'htsworkflow': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    },
}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': 'diane',
        'NAME': 'htsworkflow',
    }
}
