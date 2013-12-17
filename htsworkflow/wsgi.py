"""
WSGI config for htsworkflow project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import sys
WSGIAPP = os.path.join(os.path.dirname(__file__))

sys.path.append(os.path.abspath(os.path.join(WSGIAPP, '..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "htsworkflow.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
