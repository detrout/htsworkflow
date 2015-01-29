from django.http import HttpResponse
from django.template import RequestContext, Template, Context
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist

from . import models
from .utils import report_error, redirect_to_url
from .plugin import bcm_plugin_processor
from . import plugin
#from htsworkflow.util.jsonutil import encode_json

try:
    import json
except ImportError as e:
    import simplejson as json

import re

from htsworkflow.frontend.bcmagic import forms


def index(request):
    """
    Display a barcode magic input box
    """
    form = forms.BarcodeMagicForm()

    return render_to_response('bcmagic/magic.html', {'bcmagic': form},
                              context_instance=RequestContext(request))


def __plugin_search(text):
    """
    Runs registered plugins to search for results
    """

    hits = []
    for label, search_func in plugin._SEARCH_FUNCTIONS.items():
        result = search_func(text)
        if result is not None:
            hits.extend(result)

    n = len(hits)
    if n == 0:
        msg = 'No hits found for: %s' % (text)
        return report_error(msg)
    elif n == 1:
        return redirect_to_url(hits[0][1])
    else:
        msg = "%d hits found for (%s); multi-hit not implemented yet." % \
              (n, text)
        return report_error(msg)


    #return json.dumps(hits)


def __magic_process(text):
    """
    Based on scanned text, check to see if there is map object to use
    for a useful redirect.
    """
    # Split text on |
    split_text = text.split('|')

    # There should always be at least one | in a valid scan.
    if len(split_text) <= 1:
        #return report_error('Invalid text: %s' % (text))
        return __plugin_search(text)

    # Keyword is the first element in the list
    keyword = split_text[0]

    # Attempt to find a KeywordMap based on keyword
    try:
        keymap = models.KeywordMap.objects.get(keyword=keyword)
    except ObjectDoesNotExist(e):
        return report_error('Keyword (%s) is not defined' % (keyword))

    # Remove keyword and only scan the content
    content = '|'.join(split_text[1:])

    #FIXME: would be faster to cache compiled regex
    search = re.compile(keymap.regex)

    mo = search.search(content)

    # if the search was invalid
    if not mo:
        return report_error(
            '(%s) failed to match (%s)' % (keymap.regex, content)
        )

    t = Template(keymap.url_template)
    c = Context(mo.groupdict())

    return redirect_to_url(str(t.render(c)))


def magic(request):
    """
    Let the magic begin
    """
    d = {}

    #Retrieve posted text from processing
    if 'text' in request.POST:
        text = request.POST['text']
    else:
        text = None

    #Retrieve bmc_mode for processing
    if 'bcm_mode' in request.POST:
        bcm_mode = request.POST['bcm_mode']
    else:
        bcm_mode = None

    ################################
    # Handle some errors
    ################################

    # Did not receive text error
    if text is None or text.strip() == '':
        d['mode'] = 'Error'
        d['status'] = 'Did not recieve text'

        return HttpResponse(json.dumps(d), 'text/plain')

    # Did not receive bcm_mode error
    if bcm_mode is None or bcm_mode.strip() == '':
        d['mode'] = 'Error'
        d['status'] = 'Missing bcm_mode information'

    ################################
    # Figure out which mode to use
    ################################
    keyword = text.split('|')[0]

    # Handle URL mode by default
    if keyword == 'url':
        d['mode'] = 'redirect'
        d['url'] = text.split('|')[1]

    # Pass off processing to plugins
    elif bcm_mode != 'default':
        d = bcm_plugin_processor(keyword, text, bcm_mode)

    # Try keyword mapper
    else:
        d = __magic_process(text)

    return HttpResponse(json.dumps(d), 'text/plain')


def json_test(request):
    d = {}

    if 'text' in request.POST:
        text = request.POST['text']
    else:
        text = None

    #return HttpResponse(json.dumps(request.POST.items()), 'text/plain')
    if text is None or text.strip() == '':
        d['mode'] = 'Error'
        d['status'] = 'Did not recieve text'
        return HttpResponse(json.dumps(d), 'text/plain')

    if text.split('|')[0] == 'url':
        d['mode'] = 'redirect'
        d['url'] = text.split('|')[1]
    else:
        d['msg'] = 'Recieved text: %s' % (text)
        d['mode'] = 'clear'

    return HttpResponse(json.dumps(d), 'text/plain')
