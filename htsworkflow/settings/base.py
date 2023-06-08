"""
Django settings for wsgiexample project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from os.path import abspath, basename, dirname, join, normpath
import sys
import logging

from htsworkflow.util import config_helper


DJANGO_ROOT = dirname(dirname(abspath(__file__)))
PROJECT_ROOT = dirname(DJANGO_ROOT)

INI_OPTIONS = config_helper.HTSWConfig()

SECRET_KEY = INI_OPTIONS.setdefaultsecret('frontend', 'secret_key')
DEFAULT_API_KEY = INI_OPTIONS.setdefaultsecret('frontend', 'api')

# Default primary key field type.
# See https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-DEFAULT_AUTO_FIELD
# when changing
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# SECURITY WARNING: don't run with debug turned on in production!
# Override in settings_local
DEBUG = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [join(DJANGO_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Application definition
#AUTHENTICATION_BACKENDS = (
#  'samples.auth_backend.HTSUserModelBackend', )
#CUSTOM_USER_MODEL = 'samples.HTSUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'eland_config',
    'samples',
    'experiments.apps.Experiments',
    'bcmagic',
    'inventory',
    'labels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'htsworkflow.urls'

WSGI_APPLICATION = 'wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

EMAIL_HOST = 'localhost'

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE='America/Los_Angeles'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATICFILES_DIRS = (
    join(DJANGO_ROOT, 'static'),
)
STATIC_URL = '/static/'

###
# Application specific settings
DEFAULT_PM = 5

# How often to recheck the result archive
RESCAN_DELAY=1

# configure who is sending email and who should get BCCs of announcments
NOTIFICATION_SENDER = "noreply@example.com"
NOTIFICATION_BCC=[]

# Update this in settings_local to point to your flowcell result directory
RESULT_HOME_DIR = join(PROJECT_ROOT, 'test', 'result', 'flowcells')

LOGIN_REDIRECT_URL = '/library/'
