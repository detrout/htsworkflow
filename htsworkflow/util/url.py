"""
Utilities to help handle urls
"""

def normalize_url(url, scheme='http'):
    """
    Make sure there is a http at the head of what should be a url

    >>> normalize_url("google.com")
    'http://google.com'
    >>> normalize_url("http://google.com")
    'http://google.com'
    >>> normalize_url("foo.com/a/b/c/d/e/f.html")
    'http://foo.com/a/b/c/d/e/f.html'
    >>> normalize_url("foo.com", "https")
    'https://foo.com'
    """
    scheme_sep = '://'
    if url.find(scheme_sep) != -1:
        return url
    else:
        return scheme + scheme_sep + url
