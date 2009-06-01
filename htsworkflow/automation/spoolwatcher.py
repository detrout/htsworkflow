#!/usr/bin/env python
import logging
import os
import re
import shlex
import sys
import time
#import glob

from htsworkflow.util import mount

# this uses pyinotify
import pyinotify
from pyinotify import EventsCodes

from benderjab import rpc


def get_top_dir(root, path):
    """
    Return the directory in path that is a subdirectory of root.
    e.g.

    >>> print get_top_dir('/a/b/c', '/a/b/c/d/e/f')
    d
    >>> print get_top_dir('/a/b/c/', '/a/b/c/d/e/f')
    d
    >>> print get_top_dir('/a/b/c', '/g/e/f')
    None
    >>> print get_top_dir('/a/b/c', '/a/b/c')
    <BLANKLINE>
    """
    if path.startswith(root):
        subpath = path[len(root):]
        if subpath.startswith('/'):
            subpath = subpath[1:]
        return subpath.split(os.path.sep)[0]
    else:
        return None

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
    def __init__(self, watchmanager, bot, ipar=False):
        """
        ipar flag indicates we should wait for ipar to finish, instead of 
             just the run finishing
        """
        self.last_event = {}
        self.watchmanager = watchmanager
        self.bot = bot
        self.ipar_mode = ipar
        if self.ipar_mode:
            self.last_file = 'IPAR_Netcopy_Complete.txt'.lower()
        else:
            self.last_file = "run.completed".lower()

    def process_IN_CREATE(self, event):
        for wdd in self.bot.wdds:
            for watch_path in self.bot.watchdirs:
                if event.path.startswith(watch_path):
                    target = get_top_dir(watch_path, event.path)
                    self.last_event.setdefault(watch_path, {})[target] = time.time()

                    msg = "Create: %s %s" % (event.path, event.name)

                    if event.name.lower() == self.last_file:
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
        self.bot.unmount_watch(event.path)

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
    #    `watchdirs` - list of directories to monitor for modifications
    #    `profile` - specify which .htsworkflow profile to use
    #    `write_timeout` - how many seconds to wait for writes to finish to
    #                      the spool
    #    `notify_timeout` - how often to timeout from notify
    
    def __init__(self, section=None, configfile=None):
        #if configfile is None:
        #    self.configfile = "~/.htsworkflow"
        super(SpoolWatcher, self).__init__(section, configfile)
        
        self.cfg['watchdirs'] = None
        self.cfg['write_timeout'] = 10
        self.cfg['notify_users'] = None
        self.cfg['notify_runner'] = None
        self.cfg['wait_for_ipar'] = 0
        
        self.notify_timeout = 0.001
        self.wm = pyinotify.WatchManager()
        self.wdds = []
        # keep track if the specified mount point is currently mounted
        self.mounted_points = {}
        # keep track of which mount points tie to which watch directories
        # so maybe we can remount them.
        self.mounts_to_watches = {}
        
        self.notify_users = None
        self.notify_runner = None
        
        self.eventTasks.append(self.process_notify)

    def read_config(self, section=None, configfile=None):
        super(SpoolWatcher, self).read_config(section, configfile)
        
        self.watchdirs = shlex.split(self._check_required_option('watchdirs'))
        self.write_timeout = int(self.cfg['write_timeout'])
        self.wait_for_ipar = int(self.cfg['wait_for_ipar'])
        logging.debug('wait for ipar: ' + str(self.cfg['wait_for_ipar']))
        
        self.notify_users = self._parse_user_list(self.cfg['notify_users'])
        try:
          self.notify_runner = \
             self._parse_user_list(self.cfg['notify_runner'],
                                   require_resource=True)
        except bot.JIDMissingResource:
            msg = 'need a full jabber ID + resource for xml-rpc destinations'
            logging.FATAL(msg)
            raise bot.JIDMissingResource(msg)

        self.handler = Handler(self.wm, self, self.wait_for_ipar)
        self.notifier = pyinotify.Notifier(self.wm, self.handler)

    def add_watch(self, watchdirs=None):
        """
        start watching watchdir or self.watchdir
        we're currently limited to watching one directory tree.
        """
        # the one tree limit is mostly because self.wdd is a single item
        # but managing it as a list might be a bit more annoying
        if watchdirs is None:
            watchdirs = self.watchdirs

        mask = EventsCodes.IN_CREATE | EventsCodes.IN_UNMOUNT
        # rec traverses the tree and adds all the directories that are there
        # at the start.
        # auto_add will add in new directories as they are created
        for w in watchdirs:
            mount_location = mount.find_mount_point_for(w)
            self.mounted_points[mount_location] = True
            mounts = self.mounts_to_watches.get(mount_location, [])
            if w not in mounts:
                mounts.append(w)
                self.mounts_to_watches[mount_location] = mounts

            logging.info(u"Watching:"+unicode(w))
            self.wdds.append(self.wm.add_watch(w, mask, rec=True, auto_add=True))

    def unmount_watch(self, event_path):
        # remove backwards so we don't get weirdness from 
        # the list getting shorter
        for i in range(len(self.wdds),0, -1):
            wdd = self.wdds[i]
            logging.info(u'unmounting: '+unicode(wdd.items()))
            self.wm.rm_watch(wdd.values())
            del self.wdds[i]
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
        for watchdir, last_events in self.handler.last_event.items():
            logging.debug('last_events: %s %s' % (watchdir, last_events))
            for last_event_dir, last_event_time in last_events.items():
                time_delta = time.time() - last_event_time
                if time_delta > self.write_timeout:
                    self.startCopy(watchdir, last_event_dir)
                    self.handler.last_event[watchdir] = {}
        # handle unmounted filesystems
        for mount_point, was_mounted in self.mounted_points.items():
            if not was_mounted and mount.is_mounted(mount_point):
                # we've been remounted. Huzzah!
                # restart the watch
                for watch in self.mounts_to_watches[mount_point]:
                    self.add_watch(watch)
                    logging.info(
                        "%s was remounted, restarting watch" % \
                            (mount_point)
                    )
                self.mounted_points[mount_point] = True

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
    
    def startCopy(self, watchdir=None, event_path=None):
        logging.debug("writes seem to have stopped")
        logging.debug("watchdir = %s, event_path = %s" % (watchdir, event_path))
        if self.notify_runner is not None:
            for r in self.notify_runner:
                self.rpc_send(r, tuple(), 'startCopy')
        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, 'startCopy %s %s' % (watchdir, event_path))
        
    def sequencingFinished(self, run_dir):
        # need to strip off self.watchdirs from rundir I suspect.
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

# TODO:
# send messages to copier specifying which mount to copy
