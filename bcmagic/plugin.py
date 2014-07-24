#BCM_PLUGINS = {'cmd_move_sample': bcm_cmds.cmd_move_sample}

_SEARCH_FUNCTIONS = {}

def bcm_plugin_processor(keyword, text, bcm_mode):
    """
    Fixme should be made generic plugable, but am hard coding values for proof
    of concept.
    """
    d = {}
    
    if bcm_mode not in BCM_PLUGINS:
        d['mode'] = 'Error'
        d['status'] = 'bcm_mode plugin called "%s" was not found' % (bcm_mode)
        return d
    
    return BCM_PLUGINS[bcm_mode](keyword, text, bcm_mode)
    

def register_search_plugin(label, search_function):
    """
    Registers a group label and search_function
    
    search_function(search_string) --> (text_display, obj_url)
    """
    
    if label in _SEARCH_FUNCTIONS:
        msg = "search function for label (%s) already registered." % (label)
        raise ValueError, msg
    
    _SEARCH_FUNCTIONS[label] = search_function
    