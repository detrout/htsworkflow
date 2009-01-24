#!/usr/bin/env python
import logging
import os
import re
import sys
import time
#import glob

from htsworkflow.util import mount

# this uses pyinotify
import pyinotify
from pyinotify import EventsCodes

from benderjab import rpc


class WatcherEvents(object):
    # two events need to be tracked
    # one to send startCopy
    # one to send OMG its broken
    # OMG its broken needs to stop when we've seen enough
    #  cycles
    # this should be per runfolder. 
    # read the xml files 
    def __init__(self):
        pass
        

class Handler(pyinotify.ProcessEvent):
    def __init__(self, watchmanager, bot):
        self.last_event_time = None
        self.watchmanager = watchmanager
        self.bot = bot

    def process_IN_CREATE(self, event):
        self.last_event_time = time.time()
        msg = "Create: %s" %  os.path.join(event.path, event.name)
        if event.name.lower() == "run.completed":
            try:
                self.bot.sequencingFinished(event.path)
            except IOError, e:
                logging.error("Couldn't send sequencingFinished")
        logging.debug(msg)

    def process_IN_DELETE(self, event):
        logging.debug("Remove: %s" %  os.path.join(event.path, event.name))

    def process_IN_UNMOUNT(self, event):
        pathname = os.path.join(event.path, event.name)
        logging.debug("IN_UNMOUNT: %s" % (pathname,))
        self.bot.unmount_watch()

class SpoolWatcher(rpc.XmlRpcBot):
    """
    Watch a directory and send a message when another process is done writing.
    
    This monitors a directory tree using inotify (linux specific) and
    after some files having been written will send a message after <timeout>
    seconds of no file writing.
    
    (Basically when the solexa machine finishes dumping a round of data
    this'll hopefully send out a message saying hey look theres data available
    
    """
    # these params need to be in the config file
    # I wonder where I should put the documentation
    #:Parameters:
    #    `watchdir` - which directory tree to monitor for modifications
    #    `profile` - specify which .htsworkflow profile to use
    #    `write_timeout` - how many seconds to wait for writes to finish to
    #                      the spool
    #    `notify_timeout` - how often to timeout from notify
    
    def __init__(self, section=None, configfile=None):
        #if configfile is None:
        #    self.configfile = "~/.htsworkflow"
        super(SpoolWatcher, self).__init__(section, configfile)
        
        self.cfg['watchdir'] = None
        self.cfg['write_timeout'] = 10
        self.cfg['notify_users'] = None
        self.cfg['notify_runner'] = None
        
        self.notify_timeout = 0.001
        self.wm = pyinotify.WatchManager()
        self.handler = Handler(self.wm, self)
        self.notifier = pyinotify.Notifier(self.wm, self.handler)
        self.wdd = None
        self.mount_point = None
        self.mounted = True
        
        self.notify_users = None
        self.notify_runner = None
        
        self.eventTasks.append(self.process_notify)

    def read_config(self, section=None, configfile=None):
        super(SpoolWatcher, self).read_config(section, configfile)
        
        self.watch_dir = self._check_required_option('watchdir')
        self.write_timeout = int(self.cfg['write_timeout'])
        
        self.notify_users = self._parse_user_list(self.cfg['notify_users'])
        try:
          self.notify_runner = \
             self._parse_user_list(self.cfg['notify_runner'],
                                   require_resource=True)
        except bot.JIDMissingResource:
            msg = 'need a full jabber ID + resource for xml-rpc destinations'
            logging.FATAL(msg)
            raise bot.JIDMissingResource(msg)

    def add_watch(self, watchdir=None):
        """
        start watching watchdir or self.watch_dir
        we're currently limited to watching one directory tree.
        """
        # the one tree limit is mostly because self.wdd is a single item
        # but managing it as a list might be a bit more annoying
        if watchdir is None:
            watchdir = self.watch_dir
        logging.info("Watching:"+str(watchdir))

        self.mount_point = mount.find_mount_point_for(watchdir)

        mask = EventsCodes.IN_CREATE | EventsCodes.IN_UNMOUNT
        # rec traverses the tree and adds all the directories that are there
        # at the start.
        # auto_add will add in new directories as they are created
        self.wdd = self.wm.add_watch(watchdir, mask, rec=True, auto_add=True)

    def unmount_watch(self):
        if self.wdd is not None:
            self.wm.rm_watch(self.wdd.values())
            self.wdd = None
            self.mounted = False
            
    def process_notify(self, *args):
        # process the queue of events as explained above
        self.notifier.process_events()
        #check events waits timeout
        if self.notifier.check_events(self.notify_timeout):
            # read notified events and enqeue them
            self.notifier.read_events()
            # should we do something?
        # has something happened?
        last_event_time = self.handler.last_event_time
        if last_event_time is not None:
            time_delta = time.time() - last_event_time
            if time_delta > self.write_timeout:
                self.startCopy()
                self.handler.last_event_time = None
        # handle unmounted filesystems
        if not self.mounted:
            if mount.is_mounted(self.mount_point):
                # we've been remounted. Huzzah!
                # restart the watch
                self.add_watch()
                self.mounted = True
                logging.info(
                    "%s was remounted, restarting watch" % \
                        (self.mount_point)
                )

    def _parser(self, msg, who):
        """
        Parse xmpp chat messages
        """
        help = u"I can send [copy] message, or squencer [finished]"
        if re.match(u"help", msg):
            reply = help
        elif re.match("copy", msg):            
            self.startCopy()
            reply = u"sent copy message"
        elif re.match(u"finished", msg):
            words = msg.split()
            if len(words) == 2:
                self.sequencingFinished(words[1])
                reply = u"sending sequencing finished for %s" % (words[1])
            else:
                reply = u"need runfolder name"
        else:
            reply = u"I didn't understand '%s'" %(msg)            
        return reply
        
    def start(self, daemonize):
        """
        Start application
        """
        self.add_watch()
        super(SpoolWatcher, self).start(daemonize)
        
    def stop(self):
        """
        shutdown application
        """
        # destroy the inotify's instance on this interrupt (stop monitoring)
        self.notifier.stop()
        super(SpoolWatcher, self).stop()
    
    def startCopy(self):
        logging.debug("writes seem to have stopped")
        if self.notify_runner is not None:
            for r in self.notify_runner:
                self.rpc_send(r, tuple(), 'startCopy')
        
    def sequencingFinished(self, run_dir):
        # need to strip off self.watch_dir from rundir I suspect.
        logging.info("run.completed in " + str(run_dir))
        pattern = self.watch_dir
        if pattern[-1] != os.path.sep:
            pattern += os.path.sep
        stripped_run_dir = re.sub(pattern, "", run_dir)
        logging.debug("stripped to " + stripped_run_dir)
        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, 'Sequencing run %s finished' % (stripped_run_dir))
        if self.notify_runner is not None:
            for r in self.notify_runner:
                self.rpc_send(r, (stripped_run_dir,), 'sequencingFinished')
        
def main(args=None):
    bot = SpoolWatcher()
    return bot.main(args)
    
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

