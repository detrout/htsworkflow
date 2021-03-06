from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model

import logging
import sys

logger = logging.getLogger(__name__)

class HTSUserModelBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = self.user_class.objects.get(username=username)
            if user.check_password(password):
                return user
        #except self.user_class.DoesNotExist:
        except Exception as e:
            logger.error(str(e))
            return None

    def get_user(self, user_id):
        try:
            return self.user_class.objects.get(pk=user_id)
        #except self.user_class.DoesNotExist:
        except Exception as e:
            logger.error(str(e))
            return None

    @property
    def user_class(self):
        if not hasattr(self, '_user_class'):
            self._user_class = get_user_model()
            if not self._user_class:
                raise ImproperlyConfigured('Could not get custom user model')
            return self._user_class
