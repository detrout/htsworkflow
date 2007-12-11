#!/usr/bin/env python
import logging
import os
import re
import sys
import time

from benderjab import rpc

class Runner(rpc.XmlRpcBot):
    """
    Manage running pipeline jobs.
    """    
    def __init__(self, section=None, configfile=None):
        #if configfile is None:
        #    self.configfile = "~/.gaworkflow"
        super(Runner, self).__init__(section, configfile)
        
        self.cfg['notify_users'] = None
        
        self.register_function(self.sequencingFinished)
        self.eventTasks.append(self.update)
    
    def read_config(self, section=None, configfile=None):
        super(Runner, self).read_config(section, configfile)
    
    def _parser(self, msg, who):
        """
        Parse xmpp chat messages
        """
        help = u"I can send [start] a run, or report [status]"
        if re.match(u"help", msg):
            reply = help
        elif re.match("status", msg):            
            reply = u"not implemented"
        elif re.match(u"start", msg):
            words = msg.split()
            if len(words) == 2:
                self.sequencingFinished(words[1])
                reply = u"starting run for %s" % (words[1])
            else:
                reply = u"need runfolder name"
        else:
            reply = u"I didn't understand '%s'" %(msg)            
        return reply
        
    def start(self, daemonize):
        """
        Start application
        """
        super(Runner, self).start(daemonize)
        
    def stop(self):
        """
        shutdown application
        """
        super(Runner, self).stop()
            
    def sequencingFinished(self, run_dir):
        """
        Sequenceing (and copying) is finished, time to start pipeline
        """
        logging.debug("received sequencing finished message")
        
    def pipelineFinished(self, run_dir):
        # need to strip off self.watch_dir from rundir I suspect.
        logging.info("pipeline finished in" + str(run_dir))
        #pattern = self.watch_dir
        #if pattern[-1] != os.path.sep:
        #    pattern += os.path.sep
        #stripped_run_dir = re.sub(pattern, "", run_dir)
        #logging.debug("stripped to " + stripped_run_dir)
        #if self.notify_users is not None:
        #    for u in self.notify_users:
        #        self.send(u, 'Sequencing run %s finished' % #(stripped_run_dir))
        #if self.notify_runner is not None:
        #    for r in self.notify_runner:
        #        self.rpc_send(r, (stripped_run_dir,), 'sequencingFinished')
        
def main(args=None):
    bot = Runner()
    return bot.main(args)
    
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
    