"""Common functions for accessing the HTS Workflow REST API
"""
from __future__ import unicode_literals

import base64
import six
from six.moves import configparser
import random
import requests
import logging

import os
from six.moves import urllib

LOGGER = logging.getLogger(__name__)


def add_auth_options(parser):
    """Add options OptParser configure authentication options
    """
    # Load defaults from the config files
    config = configparser.SafeConfigParser()
    config.read([os.path.expanduser('~/.htsworkflow.ini'),
                 '/etc/htsworkflow.ini'
                 ])

    sequence_archive = None
    apiid = None
    apikey = None
    apihost = None
    SECTION = 'sequence_archive'
    if config.has_section(SECTION):
        sequence_archive = config.get(SECTION, 'sequence_archive',
                                      fallback=sequence_archive)
        sequence_archive = os.path.expanduser(sequence_archive)
        apiid = config.get(SECTION, 'apiid', fallback=apiid)
        apikey = config.get(SECTION, 'apikey', fallback=apikey)
        apihost = config.get(SECTION, 'host', fallback=apihost)

    # configuration options
    group = parser.add_argument_group("htsw api authentication")
    group.add_argument('--apiid', default=apiid, help="Specify API ID")
    group.add_argument('--apikey', default=apikey, help="Specify API KEY")
    group.add_argument('--host',  default=apihost,
                     help="specify HTSWorkflow host",)
    group.add_argument('--sequence', default=sequence_archive,
                     help="sequence repository")
    return parser

def make_auth_from_opts(opts, parser=None):
    """Create htsw auth info dictionary from optparse info
    """
    if opts.host is None or opts.apiid is None or opts.apikey is None:
        if parser is not None:
            parser.error("Please specify host url, apiid, apikey")
        else:
            raise RuntimeError("Need host, api id api key")

    return {'apiid': opts.apiid, 'apikey': opts.apikey}


def library_url(root_url, library_id):
    """
    Return the url for retrieving information about a specific library.

    Args:
      library_id (str): the library id of interest
      root_url (str): the root portion of the url, e.g. http://localhost

    Returns:
      str. The url to use for this REST api.

    >>> print library_url('http://localhost', '12345')
    http://localhost/samples/library/12345/json

    """
    url_fragment = '/library/%s/json' % (library_id,)
    url = urllib.parse.urljoin(root_url, url_fragment)

    return url


def flowcell_url(root_url, flowcell_id):
    """
    Return the url for retrieving information about a specific flowcell.

    Args:
      root_url (str): the root portion of the url, e.g. http://localhost
      flowcell_id (str): the flowcell id of interest

    Returns:
      str. The url to use for this REST api.

    >>> print flowcell_url('http://localhost', '1234AAXX')
    http://localhost/experiments/config/1234AAXX/json
    """
    url_fragment = '/experiments/config/%s/json' % (flowcell_id,)
    url = urllib.parse.urljoin(root_url, url_fragment)

    return url


def lanes_for_user_url(root_url, username):
    """
    Return the url for returning all the lanes associated with a username

    Args:
      username (str): a username in your target filesystem
      root_url (str): the root portion of the url, e.g. http://localhost

    Returns:
      str. The url to use for this REST api.

    >>> print lanes_for_user_url('http://localhost', 'diane')
    http://localhost/lanes_for/diane/json

    """
    url_fragment = '/experiments/lanes_for/%s/json' % (username,)
    url = urllib.parse.urljoin(root_url, url_fragment)

    return url

def retrieve_info(url, apidata):
    """
    Return a dictionary from the HTSworkflow API
    """
    web = requests.get(url, params=apidata)

    if web.status_code != 200:
        raise requests.HTTPError(
            "Failed to access {} error {}".format(url, web.status_code))

    result = web.json()
    if "result" in result:
        result = result["result"]
    return result

class HtswApi(object):
    def __init__(self, root_url, authdata):
        self.root_url = root_url
        self.authdata = authdata

    def get_flowcell(self, flowcellId):
        url = flowcell_url(self.root_url, flowcellId)
        return retrieve_info(url, self.authdata)

    def get_library(self, libraryId):
        url = library_url(self.root_url, libraryId)
        return retrieve_info(url, self.authdata)

    def get_lanes_for_user(self, user):
        url = lanes_for_user(self.root_url, user)
        return retrieve_info(url, self.authdata)

    def get_url(self, url):
        return retrieve_info(url, self.authdata)

def make_django_secret_key(size=216):
    """return key suitable for use as secret key"""
    try:
        source = random.SystemRandom()
    except AttributeError as e:
        source = random.random()
    bits = source.getrandbits(size)
    chars = []
    while bits > 0:
        byte = bits & 0xff
        chars.append(six.int2byte(byte))
        bits >>= 8

    raw_bytes = base64.encodebytes(b"".join(chars)).strip()
    if six.PY3:
        return raw_bytes.decode('ascii')
    else:
        return raw_bytes

if __name__ == "__main__":
    from optparse import OptionParser
    from pprint import pprint
    parser = OptionParser()
    parser = add_auth_options(parser)
    parser.add_option('--flowcell', default=None)
    parser.add_option('--library', default=None)

    opts, args = parser.parse_args()
    apidata = make_auth_from_opts(opts)

    api = HtswApi(opts.host, apidata)

    if opts.flowcell is not None:
        pprint(api.get_flowcell(opts.flowcell))
    if opts.library is not None:
        pprint(api.get_library(opts.library))

