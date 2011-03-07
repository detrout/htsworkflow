"""Utilities to help process solexa/illumina runfolders
"""
import os
import re

def is_runfolder(name):
    """
    Is it a runfolder?

    >>> print is_runfolder('090630_HWUSI-EAS999_0006_30LNFAAXX')
    True
    >>> print is_runfolder('hello')
    False
    """
    if re.match("^[0-9]{6}_[-A-Za-z0-9_]*$", name):
        return True
    else:
        return False

def get_top_dir(root, path):
    """
    Return the directory in path that is a subdirectory of root.
    e.g.

    >>> print get_top_dir('/a/b/c', '/a/b/c/d/e/f')
    d
    >>> print get_top_dir('/a/b/c/', '/a/b/c/d/e/f')
    d
    >>> print get_top_dir('/a/b/c', '/g/e/f')
    None
    >>> print get_top_dir('/a/b/c', '/a/b/c')
    <BLANKLINE>
    """
    if path.startswith(root):
        subpath = path[len(root):]
        if subpath.startswith('/'):
            subpath = subpath[1:]
        return subpath.split(os.path.sep)[0]
    else:
        return None

