"""
Common functions for accessing the HTS Workflow REST API

"""
import logging

# try to deal with python <2.6
try:
  import json
except ImportError:
  import simplejson as json

import urllib
import urllib2
import urlparse

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
    url_fragment = '/samples/library/%s/json' % (library_id,)
    url = urlparse.urljoin(root_url, url_fragment)

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
    url = urlparse.urljoin(root_url, url_fragment)

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
    url_fragment = '/lanes_for/%s/json' % (username,)
    url = urlparse.urljoin(root_url, url_fragment)

    return url

def retrieve_info(url, apidata):
    """
    Return a dictionary from the HTSworkflow API
    """
    try:
        apipayload = urllib.urlencode(apidata)
        web = urllib2.urlopen(url, apipayload)
    except urllib2.URLError, e:
        if hasattr(e, 'code') and e.code == 404:
            logging.info("%s was not found" % (url,))
            return None
        else:
            errmsg = 'URLError: %s' % (str(e))
            raise IOError(errmsg)
    
    contents = web.read()
    headers = web.info()

    return json.loads(contents)
