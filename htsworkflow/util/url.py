"""
Utilities to help handle urls
"""
import collections

def normalize_url(url, scheme='http'):
    """
    Make sure there is a http at the head of what should be a url
    """
    # not much to do with None except avoid an exception
    if url is None:
        return None
    
    scheme_sep = '://'
    if url.find(scheme_sep) != -1:
        return url
    else:
        return scheme + scheme_sep + url

SSHURL = collections.namedtuple("SSHURL", "user host path")

def parse_ssh_url(url):
    """Parse scp-style username, host and path.
    """
    # simple initialization
    user = None
    host = None
    path = None
    
    colon = url.find(':')
    if colon == -1:
        raise ValueError("Invalid SSH URL: need <host>:<path>")
    
    path = url[colon+1:]
    
    user_host = url[:colon]
    atsign = user_host.find('@')
    if atsign != -1:
        user = user_host[:atsign]
        host = user_host[atsign+1:]
    else:
        host = user_host

    return SSHURL(user, host, path)
    
