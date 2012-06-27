"""
Generate settings for the Django Application.

To make it easier to customize the application the settings can be
defined in a configuration file read by ConfigParser.

The options understood by this module are (with their defaults):

  [frontend]
  email_host=localhost
  email_port=25
  database=<section_name>

  [database_name]
  engine=sqlite3
  name=/path/to/database

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
import htsworkflow
import django
from django.conf import global_settings

from htsworkflow.util.api import make_django_secret_key

HTSWORKFLOW_ROOT = os.path.abspath(os.path.split(htsworkflow.__file__)[0])

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
options = ConfigParser.SafeConfigParser()

def save_options(filename, options):
    try:
        ini_stream = open(filename, 'w')
        options.write(ini_stream)
        ini_stream.close()
    except IOError, e:
        LOGGER.debug("Error saving setting: %s" % (str(e)))

INI_FILE = options.read([os.path.expanduser("~/.htsworkflow.ini"),
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

if options.has_option('front', 'default_pm'):
    DEFAULT_PM=int(options.get('frontend', 'default_pm'))
else:
    DEFAULT_PM=5

AUTHENTICATION_BACKENDS = (
  'htsworkflow.frontend.samples.auth_backend.HTSUserModelBackend', )
CUSTOM_USER_MODEL = 'samples.HTSUser'

EMAIL_HOST = options.get('frontend', 'email_host', 'localhost')
EMAIL_PORT = int(options.get('frontend', 'email_port', 25))

if options.has_option('frontend', 'notification_sender'):
    NOTIFICATION_SENDER = options.get('frontend', 'notification_sender')
else:
    NOTIFICATION_SENDER = "noreply@example.com"
NOTIFICATION_BCC = []
options_to_list(options, NOTIFICATION_BCC, 'frontend', 'notification_bcc')

database_section = options.get('frontend', 'database', 'database')

if not options.has_section(database_section):
    raise ConfigParser.NoSectionError(
        "No database=<database_section_name> defined")

# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_ENGINE = options.get(database_section, 'engine')
DATABASE_NAME = options.get(database_section, 'name')
if options.has_option(database_section, 'user'):
    DATABASE_USER = options.get(database_section, 'user')
if options.has_option(database_section, 'host'):
    DATABASE_HOST = options.get(database_section, 'host')
if options.has_option(database_section, 'port'):
    DATABASE_PORT = options.get(database_section, 'port')

if options.has_option(database_section, 'password_file'):
    password_file = options.get(database_section, 'password_file')
    DATABASE_PASSWORD = open(password_file,'r').readline()
elif options.has_option(database_section, 'password'):
    DATABASE_PASSWORD = options.get(database_section, 'password')

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
if options.has_option('frontend', 'time_zone'):
  TIME_ZONE = options.get('frontend', 'time_zone')
else:
  TIME_ZONE = 'America/Los_Angeles'

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
MEDIA_ROOT = os.path.join(HTSWORKFLOW_ROOT, 'frontend', 'static', '')

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
if not options.has_option('frontend', 'secret'):
    options.set('frontend', 'secret_key', make_django_secret_key(458))
    save_options(INI_FILE[0], options)
SECRET_KEY = options.get('frontend', 'secret_key')

# some of our urls need an api key
DEFAULT_API_KEY = 'n7HsXGHIi0vp9j5u4TIRJyqAlXYc4wrH'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'htsworkflow.frontend.thispage.thispage',
)
ROOT_URLCONF = 'htsworkflow.frontend.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/usr/share/python-support/python-django/django/contrib/admin/templates',
    #'/usr/lib/pymodules/python2.6/django/contrib/admin/templates/',
    os.path.join(HTSWORKFLOW_ROOT, 'frontend', 'templates'),
    os.path.join(HTSWORKFLOW_ROOT, 'templates'),
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
    'htsworkflow.frontend.labels',
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
# Where "results_dir" means directory with all the flowcells
if options.has_option('frontend', 'results_dir'):
    RESULT_HOME_DIR=os.path.expanduser(options.get('frontend', 'results_dir'))
else:
    RESULT_HOME_DIR='/tmp'

if options.has_option('frontend', 'link_flowcell_storage_device_url'):
    LINK_FLOWCELL_STORAGE_DEVICE_URL = options.get('frontend',
                                                   'link_flowcell_storage_device_url')
else:
    LINK_FLOWCELL_STORAGE_DEVICE_URL = None
# PORT 9100 is default for Zebra tabletop/desktop printers
# PORT 6101 is default for Zebra mobile printers
BCPRINTER_PRINTER1_HOST = options.get('bcprinter', 'printer1_host')
BCPRINTER_PRINTER1_PORT = int(options.get('bcprinter', 'printer1_port'))
BCPRINTER_PRINTER2_HOST = options.get('bcprinter', 'printer2_host')
BCPRINTER_PRINTER2_PORT = int(options.get('bcprinter', 'printer2_port'))

