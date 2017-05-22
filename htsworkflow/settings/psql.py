# -*- mode: python; coding: utf-8; python-indent-offset: 4; -*-
import os
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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        #'HOST': 'localhost',
        #'USER': os.getlogin(),
        #'NAME': '/var/run/postgresql/9.6-main.pg_stat_tmp',
        #'NAME': 'htsworkflow',
        #'PASSWORD': '',
    }
}
