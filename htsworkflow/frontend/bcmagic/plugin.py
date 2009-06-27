#from htsworkflow.frontend.samples import bcm_cmds

#BCM_PLUGINS = {'cmd_move_sample': bcm_cmds.cmd_move_sample}


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