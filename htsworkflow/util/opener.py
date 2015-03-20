"""
Helpful utilities for turning random names/objects into streams.
"""
import os
import gzip
import bz2
import six
from six.moves import urllib

if six.PY2:
    import types
    FILE_CLASS = types.FileType
else:
    import io
    FILE_CLASS = io.IOBase

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
    elif isurllike(file_ref, mode):
        return urllib.request.urlopen(file_ref)
    elif os.path.splitext(file_ref)[1] == ".gz":
        return gzip.open(file_ref, mode)
    elif os.path.splitext(file_ref)[1] == '.bz2':
        return bz2.BZ2File(file_ref, mode)
    else:
        return open(file_ref,mode)

