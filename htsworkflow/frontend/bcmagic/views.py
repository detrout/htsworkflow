from django.http import HttpResponse
from django.template import RequestContext, Template, Context
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist

from htsworkflow.frontend.bcmagic import models
from htsworkflow.frontend.bcmagic.utils import report_error, redirect_to_url
from htsworkflow.frontend.bcmagic.plugin import bcm_plugin_processor
from htsworkflow.util.jsonutil import encode_json

import re

from htsworkflow.frontend.bcmagic import forms

def index(request):
    """
    Display a barcode magic input box
    """
    form = forms.BarcodeMagicForm()
    
    return render_to_response('bcmagic/magic.html', {'bcmagic': form},
                              context_instance=RequestContext(request))


def __magic_process(text):
    """
    Based on scanned text, check to see if there is map object to use
    for a useful redirect.
    """
    # Split text on |
    split_text = text.split('|')
    
    # There should always be at least one | in a valid scan.
    if len(split_text) <= 1:
        return report_error('Invalid text: %s' % (text))
    
    # Keyword is the first element in the list
    keyword = split_text[0]
    
    # Attempt to find a KeywordMap based on keyword
    try:
        keymap = models.KeywordMap.objects.get(keyword=keyword)
    except ObjectDoesNotExist, e:
        return report_error('Keyword (%s) is not defined' % (keyword))
    
    # Remove keyword and only scan the content
    content = '|'.join(split_text[1:])
    
    #FIXME: would be faster to cache compiled regex
    search = re.compile(keymap.regex)
    
    mo = search.search(content)
    
    # if the search was invalid
    if not mo:
        return report_error('(%s) failed to match (%s)' % (keymap.regex, content))
    
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
        j = json.JSONEncoder()
        return HttpResponse(j.encode(d), 'text/plain')
    
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
    
    return HttpResponse(encode_json(d), 'text/plain')



def json_test(request):
    d = {}
    
    if 'text' in request.POST:
        text = request.POST['text']
    else:
        text = None
    
    #return HttpResponse(encode_json(request.POST.items()), 'text/plain')
    if text is None or text.strip() == '':
        d['mode'] = 'Error'
        d['status'] = 'Did not recieve text'
        return HttpResponse(encode_json(d), 'text/plain')
    
    if text.split('|')[0] == 'url':
        d['mode'] = 'redirect'
        d['url'] = text.split('|')[1]
    else:
        d['msg'] = 'Recieved text: %s' % (text)
        d['mode'] = 'clear'
    
    return HttpResponse(json_encode(d), 'text/plain')
