"""
Generate settings for the Django Application.

To make it easier to customize the application the settings can be 
defined in a configuration file read by ConfigParser.

The options understood by this module are (with their defaults):

  [frontend]
  email_host=localhost
  email_port=25
  database_engine=sqlite3
  database_name=/path/to/db

  [admins]
  #name1=email1

  [allowed_hosts]
  #name1=ip
  localhost=127.0.0.1
  
  [allowed_analysis_hosts]
  #name1=ip
  localhost=127.0.0.1

"""
import ConfigParser
import os
import shlex

# make epydoc happy
__docformat__ = "restructuredtext en"

def options_to_list(options, dest, section_name, option_name):
  """
  Load a options from section_name and store in a dictionary
  """
  if options.has_option(section_name, option_name):
    opt = options.get(section_name, option_name)
    dest.extend( shlex.split(opt) )
      
def options_to_dict(dest, section_name):
  """
  Load a options from section_name and store in a dictionary
  """
  if options.has_section(section_name):
    for name in options.options(section_name):
      dest[name] = options.get(section_name, name)

# define your defaults here
options = ConfigParser.SafeConfigParser(
           { 'email_host': 'localhost',
             'email_port': '25', 
             'database_engine': 'sqlite3',
             'database_name': 
               os.path.abspath('../../fctracker.db'),
             'time_zone': 'America/Los_Angeles',
             'default_pm': '5',
             'link_flowcell_storage_device_url': "http://localhost:8000/inventory/lts/link/",
             'printer1_host': '127.0.0.1',
             'printer1_port': '9100',
             'printer2_host': '127.0.0.1',
             'printer2_port': '9100',
           })

options.read([os.path.expanduser("~/.htsworkflow.ini"),
              '/etc/htsworkflow.ini',])

# OptionParser will use the dictionary passed into the config parser as
# 'Default' values in any section. However it still needs an empty section
# to exist in order to retrieve anything.
if not options.has_section('frontend'):
    options.add_section('frontend')
if not options.has_section('bcprinter'):
    options.add_section('bcprinter')


# Django settings for elandifier project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = []
options_to_list(options, ADMINS, 'frontend', 'admins')

MANAGERS = []
options_to_list(options, MANAGERS, 'frontend', 'managers')

AUTHENTICATION_BACKENDS = ( 'samples.auth_backend.HTSUserModelBackend', )
CUSTOM_USER_MODEL = 'samples.HTSUser' 

EMAIL_HOST = options.get('frontend', 'email_host')
EMAIL_PORT = int(options.get('frontend', 'email_port'))

if options.has_option('frontend', 'notification_sender'):
    NOTIFICATION_SENDER = options.get('frontend', 'notification_sender')
else:
    NOTIFICATION_SENDER = "noreply@example.com"

# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_ENGINE = options.get('frontend', 'database_engine')

# Or path to database file if using sqlite3.
DATABASE_NAME = options.get('frontend', 'database_name' )
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = options.get('frontend', 'time_zone')

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.abspath(os.path.split(__file__)[0]) + '/static/'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(ekv^=gf(j9f(x25@a7r+8)hqlz%&_1!tw^75l%^041#vi=@4n'

# some of our urls need an api key
DEFAULT_API_KEY = 'n7HsXGHIi0vp9j5u4TIRJyqAlXYc4wrH'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'htsworkflow.frontend.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/usr/lib/pymodules/python2.6/django/contrib/admin/templates/',
    os.path.join(os.path.split(__file__)[0], 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'htsworkflow.frontend.eland_config',
    'htsworkflow.frontend.samples',
    # modules from htsworkflow branch
    'htsworkflow.frontend.experiments',
    'htsworkflow.frontend.analysis', 
    'htsworkflow.frontend.reports',
    'htsworkflow.frontend.inventory',
    'htsworkflow.frontend.bcmagic',
    'django.contrib.databrowse',
)

# Project specific settings

ALLOWED_IPS={'127.0.0.1': '127.0.0.1'}
options_to_dict(ALLOWED_IPS, 'allowed_hosts')

ALLOWED_ANALYS_IPS = {'127.0.0.1': '127.0.0.1'}
options_to_dict(ALLOWED_ANALYS_IPS, 'allowed_analysis_hosts')
#UPLOADTO_HOME = os.path.abspath('../../uploads')
#UPLOADTO_CONFIG_FILE = os.path.join(UPLOADTO_HOME, 'eland_config')
#UPLOADTO_ELAND_RESULT_PACKS = os.path.join(UPLOADTO_HOME, 'eland_results')
#UPLOADTO_BED_PACKS = os.path.join(UPLOADTO_HOME, 'bed_packs')
RESULT_HOME_DIR='/Users/diane/proj/solexa/results/flowcells'

LINK_FLOWCELL_STORAGE_DEVICE_URL = options.get('frontend', 'link_flowcell_storage_device_url')
# PORT 9100 is default for Zebra tabletop/desktop printers
# PORT 6101 is default for Zebra mobile printers
BCPRINTER_PRINTER1_HOST = options.get('bcprinter', 'printer1_host')
BCPRINTER_PRINTER1_PORT = int(options.get('bcprinter', 'printer1_port'))
BCPRINTER_PRINTER2_HOST = options.get('bcprinter', 'printer2_host')
BCPRINTER_PRINTER2_PORT = int(options.get('bcprinter', 'printer2_port'))
