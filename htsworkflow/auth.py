"""
Define some alternate authentication methods
"""
from django.core.exceptions import PermissionDenied
from django.conf import settings

apidata = {'apiid': u'0', 'apikey': settings.DEFAULT_API_KEY}

def require_api_key(request):
    # make sure we have the api component
    if not ('apiid' in request.GET or 'apikey' in request.GET):
        raise PermissionDenied

    # make sure the id and key are right
    if request.GET['apiid'] == apidata['apiid'] and \
       request.GET['apikey'] == apidata['apikey']:
        return True
    else:
        raise PermissionDenied
