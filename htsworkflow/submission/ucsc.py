"""Utilities for extracting information from the ENCODE DCC
"""
import urlparse
import urllib2

UCSCEncodePipeline = "http://encodesubmit.ucsc.edu/pipeline/"


def ddf_download_url(submission_id):
    """Return url to download a DDF for a submission

    >>> ddf_download_url(1234)
    'http://encodesubmit.ucsc.edu/pipeline/download_ddf/1234'
    """
    fragment = 'download_ddf/%s' % (submission_id,)
    return urlparse.urljoin(UCSCEncodePipeline, fragment)


def daf_download_url(submission_id):
    """Return url to download a DAF for a submission

    >>> daf_download_url(1234)
    'http://encodesubmit.ucsc.edu/pipeline/download_daf/1234'
    """
    fragment = 'download_daf/%s' % (submission_id,)
    return urlparse.urljoin(UCSCEncodePipeline, fragment)


def submission_view_url(submission_id):
    """Return url to download a DAF for a submission

    >>> submission_view_url(1234)
    'http://encodesubmit.ucsc.edu/pipeline/show/1234'
    """
    fragment = 'show/%s' % (submission_id,)
    return urlparse.urljoin(UCSCEncodePipeline, fragment)


def get_ucsc_file_index(base_url):
    """Get index of files for a ENCODE collection
    """
    if base_url[-1] != '/': base_url += '/'
    request = urllib2.urlopen(base_url + 'files.txt')
    file_index = parse_ucsc_file_index(request)
    return file_index


def parse_ucsc_file_index(stream):
    """Turn a UCSC DCC files.txt index into a dictionary of name-value pairs
    """
    file_index = {}
    for line in stream:
        filename, attribute_line = line.split('\t')
        attributes = {}
        for assignment in  attribute_line.split(';'):
            name, value = assignment.split('=')
            attributes[name.strip()] = value.strip()

        file_index[filename] = attributes
    return file_index
