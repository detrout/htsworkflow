"""
Django settings for wsgiexample project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'c=5&609$7)bm_u+3$2bi=ida$*a)c1(cp_0siua7uyww!1qfg_'

DEFAULT_API_KEY = 'n7HsXGHIi0vp9j5u4TIRJyqAlXYc4wrH'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['jumpgate.caltech.edu']


# Application definition
AUTHENTICATION_BACKENDS = (
  'htsworkflow.frontend.samples.auth_backend.HTSUserModelBackend', )
CUSTOM_USER_MODEL = 'samples.HTSUser'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'htsworkflow.frontend.eland_config',
    'htsworkflow.frontend.samples',
    'htsworkflow.frontend.experiments',
    'htsworkflow.frontend.inventory',
    'htsworkflow.frontend.bcmagic',
    'htsworkflow.frontend.labels',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'htsworkflow', 'frontend', 'templates'),
    os.path.join(BASE_DIR, 'htsworkflow', 'templates'),
)

ROOT_URLCONF = 'htsworkflow.frontend.urls'

WSGI_APPLICATION = 'htsworkflow.frontend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'fctracker.db'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'


#####
# Application specific settings
# Update this in settings_local to point to your flowcell result directory
RESULT_HOME_DIR = os.path.join(BASE_DIR, 'test', 'results')

try:
    # allow local customizations
    from settings_local import *
except ImportError as e:
    pass
