#!/usr/bin/env python
import logging
import os
import re
import sys
import time
import threading

from benderjab import rpc

from gaworkflow.pipeline.configure_run import *
from gaworkflow.pipeline.monitors import _percentCompleted

#s_fc = re.compile('FC[0-9]+')
s_fc = re.compile('_[0-9a-zA-Z]*$')


def _get_flowcell_from_rundir(run_dir):
    """
    Returns flowcell string based on run_dir.
    Returns None and logs error if flowcell can't be found.
    """
    junk, dirname = os.path.split(run_dir)
    mo = s_fc.search(dirname)
    if not mo:
        logging.error('RunDir 2 FlowCell error: %s' % (run_dir))
        return None

    return dirname[mo.start()+1:]
    


class Runner(rpc.XmlRpcBot):
    """
    Manage running pipeline jobs.
    """    
    def __init__(self, section=None, configfile=None):
        #if configfile is None:
        #    self.configfile = "~/.gaworkflow"
        super(Runner, self).__init__(section, configfile)
        
        self.cfg['notify_users'] = None
        self.cfg['genome_dir'] = None
        self.cfg['base_analysis_dir'] = None

        self.cfg['notify_users'] = None
        self.cfg['notify_postanalysis'] = None

        self.conf_info_dict = {}
        
        self.register_function(self.sequencingFinished)
        #self.eventTasks.append(self.update)

    
    def read_config(self, section=None, configfile=None):
        super(Runner, self).read_config(section, configfile)

        self.genome_dir = self._check_required_option('genome_dir')
        self.base_analysis_dir = self._check_required_option('base_analysis_dir')

        self.notify_users = self._parse_user_list(self.cfg['notify_users'])
        #FIXME: process notify_postpipeline cfg
        
    
    def _parser(self, msg, who):
        """
        Parse xmpp chat messages
        """
        help = u"I can send [start] a run, or report [status]"
        if re.match(u"help", msg):
            reply = help
        elif re.match("status", msg):
            words = msg.split()
            if len(words) == 2:
                reply = self.getStatusReport(words[1])
            else:
                reply = u"Status available for: %s" \
                        % (', '.join([k for k in self.conf_info_dict.keys()]))
        elif re.match(u"start", msg):
            words = msg.split()
            if len(words) == 2:
                self.sequencingFinished(words[1])
                reply = u"starting run for %s" % (words[1])
            else:
                reply = u"need runfolder name"
        else:
            reply = u"I didn't understand '%s'" %(msg)

        logging.debug("reply: " + str(reply))
        return reply


    def getStatusReport(self, fc_num):
        """
        Returns text status report for flow cell number 
        """
        if fc_num not in self.conf_info_dict:
            return "No record of a %s run." % (fc_num)

        status = self.conf_info_dict[fc_num].status

        if status is None:
            return "No status information for %s yet." \
                   " Probably still in configure step. Try again later." % (fc_num)

        fc,ft = status.statusFirecrest()
        bc,bt = status.statusBustard()
        gc,gt = status.statusGerald()

        tc,tt = status.statusTotal()

        fp = _percentCompleted(fc, ft)
        bp = _percentCompleted(bc, bt)
        gp = _percentCompleted(gc, gt)
        tp = _percentCompleted(tc, tt)

        output = []

        output.append(u'Firecrest: %s%% (%s/%s)' % (fp, fc, ft))
        output.append(u'  Bustard: %s%% (%s/%s)' % (bp, bc, bt))
        output.append(u'   Gerald: %s%% (%s/%s)' % (gp, gc, gt))
        output.append(u'-----------------------')
        output.append(u'    Total: %s%% (%s/%s)' % (tp, tc, tt))

        return '\n'.join(output)
    
            
    def sequencingFinished(self, run_dir):
        """
        Sequenceing (and copying) is finished, time to start pipeline
        """
        logging.debug("received sequencing finished message")

        # Setup config info object
        ci = ConfigInfo()
        ci.base_analysis_dir = self.base_analysis_dir
        ci.analysis_dir = os.path.join(self.base_analysis_dir, run_dir)        

        # get flowcell from run_dir name
        flowcell = _get_flowcell_from_rundir(run_dir)

        # Store ci object in dictionary
        self.conf_info_dict[flowcell] = ci


        # Launch the job in it's own thread and turn.
        self.launchJob(run_dir, flowcell, ci)
        
        
    def pipelineFinished(self, run_dir):
        # need to strip off self.watch_dir from rundir I suspect.
        logging.info("pipeline finished in" + str(run_dir))
        #pattern = self.watch_dir
        #if pattern[-1] != os.path.sep:
        #    pattern += os.path.sep
        #stripped_run_dir = re.sub(pattern, "", run_dir)
        #logging.debug("stripped to " + stripped_run_dir)

        # Notify each user that the run has finished.
        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, 'Pipeline run %s finished' % (run_dir))
                
        #if self.notify_runner is not None:
        #    for r in self.notify_runner:
        #        self.rpc_send(r, (stripped_run_dir,), 'sequencingFinished')

    def reportMsg(self, msg):

        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, msg)


    def _runner(self, run_dir, flowcell, conf_info):

        # retrieve config step
        cfg_filepath = os.path.join(conf_info.analysis_dir,
                                    'config32auto.txt')
        status_retrieve_cfg = retrieve_config(conf_info,
                                          flowcell,
                                          cfg_filepath,
                                          self.genome_dir)
        if status_retrieve_cfg:
            logging.info("Runner: Retrieve config: success")
            self.reportMsg("Retrieve config (%s): success" % (run_dir))
        else:
            logging.error("Runner: Retrieve config: failed")
            self.reportMsg("Retrieve config (%s): FAILED" % (run_dir))

        
        # configure step
        if status_retrieve_cfg:
            status = configure(conf_info)
            if status:
                logging.info("Runner: Configure: success")
                self.reportMsg("Configure (%s): success" % (run_dir))
            else:
                logging.error("Runner: Configure: failed")
                self.reportMsg("Configure (%s): FAILED" % (run_dir))

            #if successful, continue
            if status:
                # Setup status cmdline status monitor
                #startCmdLineStatusMonitor(ci)
                
                # running step
                print 'Running pipeline now!'
                run_status = run_pipeline(conf_info)
                if run_status is True:
                    logging.info('Runner: Pipeline: success')
                    self.piplineFinished(run_dir)
                else:
                    logging.info('Runner: Pipeline: failed')
                    self.reportMsg("Pipeline run (%s): FAILED" % (run_dir))


    def launchJob(self, run_dir, flowcell, conf_info):
        """
        Starts up a thread for running the pipeline
        """
        t = threading.Thread(target=self._runner,
                        args=[run_dir, flowcell, conf_info])
        t.setDaemon(True)
        t.start()
        

        
def main(args=None):
    bot = Runner()
    return bot.main(args)
    
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
    
