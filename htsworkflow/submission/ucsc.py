"""Utilities for extracting information from the ENCODE DCC
"""
import logging
from six.moves import urllib

LOGGER = logging.getLogger(__name__)

UCSCEncodePipeline = "http://encodesubmit.ucsc.edu/pipeline/"

GOLDEN_PATHS = ["http://hgdownload-test.cse.ucsc.edu/goldenPath/"\
                "{genome}/encodeDCC/{composite}/",
                "http://hgdownload.cse.ucsc.edu/goldenPath/"\
                "{genome}/encodeDCC/{composite}/"]


def ddf_download_url(submission_id):
    """Return url to download a DDF for a submission

    >>> ddf_download_url(1234)
    'http://encodesubmit.ucsc.edu/pipeline/download_ddf/1234'
    """
    fragment = 'download_ddf/%s' % (submission_id,)
    return urllib.parse.urljoin(UCSCEncodePipeline, fragment)


def daf_download_url(submission_id):
    """Return url to download a DAF for a submission

    >>> daf_download_url(1234)
    'http://encodesubmit.ucsc.edu/pipeline/download_daf/1234'
    """
    fragment = 'download_daf/%s' % (submission_id,)
    return urllib.parse.urljoin(UCSCEncodePipeline, fragment)


def submission_view_url(submission_id):
    """Return url to download a DAF for a submission

    >>> submission_view_url(1234)
    'http://encodesubmit.ucsc.edu/pipeline/show/1234'
    """
    fragment = 'show/%s' % (submission_id,)
    return urllib.parse.urljoin(UCSCEncodePipeline, fragment)


def get_encodedcc_file_index(genome, composite):
    """Get index of files for a ENCODE collection

    returns None on error
    """
    err = None
    params = {'genome': genome,
              'composite': composite}

    for path in GOLDEN_PATHS:
        base_url = path.format(**params)
        request_url = base_url + 'files.txt'

        try:
            request = urllib.request.urlopen(request_url)
            file_index = parse_ucsc_file_index(request, base_url)
            return file_index
        except urllib.error.HTTPError as e:
            err = e
            pass

    if err is not None:
        errmsg = "get_ucsc_file_index <{0}>: {1}"
        LOGGER.error(errmsg.format(request_url, str(e)))

    return None


def parse_ucsc_file_index(stream, base_url):
    """Turn a UCSC DCC files.txt index into a dictionary of name-value pairs
    """
    file_index = {}
    for line in stream:
        filename, attribute_line = line.split('\t')
        filename = base_url + filename
        attributes = {}
        for assignment in  attribute_line.split(';'):
            name, value = assignment.split('=')
            attributes[name.strip()] = value.strip()

        file_index[filename] = attributes
    return file_index
