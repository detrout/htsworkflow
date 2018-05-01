"""
Helpful utilities for turning random names/objects into streams.
"""
import os
import gzip
import bz2
import six
from six.moves import urllib
import requests

if six.PY2:
    import types
    FILE_CLASS = types.FileType
else:
    import io
    FILE_CLASS = io.IOBase

GZIP_MIME_TYPES = ['application/gzip', 'application/x-gzip']

def isfilelike(file_ref, mode):
    """Does file_ref have the core file operations?
    """
    # if mode is w/a check to make sure we writeable ops
    # but always check to see if we can read
    read_operations = ['read', 'readline', 'readlines']
    write_operations = [ 'write', 'writelines' ]
    #random_operations = [ 'seek', 'tell' ]
    if mode[0] in ('w', 'a'):
        for o in write_operations:
            if not hasattr(file_ref, o):
                return False
    for o in read_operations:
        if not hasattr(file_ref, o):
            return False
          
    return True

def isurllike(file_ref, mode):
    """
    does file_ref look like a url?
    (AKA does it start with protocol:// ?)
    """
    #what if mode is 'w'?
    parsed = urllib.parse.urlparse(file_ref)
    schema, netloc, path, params, query, fragment = parsed
    
    return len(schema) > 0

def autoopen(file_ref, mode='r'):
    """
    Attempt to intelligently turn file_ref into a readable stream
    """
    # catch being passed a file
    if isinstance(file_ref, FILE_CLASS):
        return file_ref
    # does it look like a file?
    elif isfilelike(file_ref, mode):
        return file_ref

    if isurllike(file_ref, mode):
        response = requests.get(file_ref, stream=True)
        content_type = response.headers['content-type'].split(';', 1)[0]

        if 't' in mode and content_type in GZIP_MIME_TYPES:
            if six.PY2:
                raise RuntimeError('Gunzipping on the fly requires Python 3')
            return gzip.open(response.raw, mode)
        return response.raw
    elif os.path.splitext(file_ref)[1] == ".gz":
        return gzip.open(file_ref, mode)
    elif os.path.splitext(file_ref)[1] == '.bz2':
        return bz2.BZ2File(file_ref, mode)
    else:
        return open(file_ref,mode)
