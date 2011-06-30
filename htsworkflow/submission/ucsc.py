import urlparse

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
