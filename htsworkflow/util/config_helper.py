"""Helper functions to manage ini file settings.
"""
import logging
import os
from six.moves import configparser

from htsworkflow.util.api import make_django_secret_key

LOGGER = logging.getLogger(__name__)


class HTSWConfig(configparser.SafeConfigParser):
    '''Customization of SafeConfigParser that can open and save itself.
    '''
    def __init__(self, path=[os.path.expanduser("~/.htsworkflow.ini"),
                             '/etc/htsworkflow.ini']):
        # ConfigParser isn't a new-style class? lame
        # super(configparser.SafeConfigParser, self).__init__()
        configparser.SafeConfigParser.__init__(self)
        read_path = self.read(path)
        if len(read_path) > 0:
            self.filename = read_path[0]
        else:
            self.filename = path[0]

    def setdefaultsecret(self, section, key, length=216):
        '''return current secret key, creating a new key if needed
        '''
        if not self.has_section(section):
            self.add_section(section)

        if not self.has_option(section, key):
            secret = make_django_secret_key(length)
            self.set(section, key, secret)
            self.save()
        return self.get(section, key)

    def save(self):
        try:
            ini_stream = open(self.filename, 'w')
            self.write(ini_stream)
            ini_stream.close()
        except IOError as e:
            LOGGER.info("Error saving setting: %s" % (str(e)))
