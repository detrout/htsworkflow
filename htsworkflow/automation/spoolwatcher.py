#!/usr/bin/env python
import logging
import os
import re
import shlex
import sys
import time

from htsworkflow.util import mount

# this uses pyinotify
import pyinotify
from pyinotify import EventsCodes
IN_CREATE = EventsCodes.ALL_FLAGS['IN_CREATE']
IN_UNMOUNT = EventsCodes.ALL_FLAGS['IN_UNMOUNT']

from benderjab import rpc

def is_runfolder(name):
    """
    Is it a runfolder?

    >>> print is_runfolder('090630_HWUSI-EAS999_0006_30LNFAAXX')
    True
    >>> print is_runfolder('hello')
    False
    """
    if re.match("[0-9]{6}_.*", name):
        return True
    else:
        return False

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

class WatcherEvent(object):
    """
    Track information about a file event

    Currently its time, and if it was an indication we've completed the run.
    """
    def __init__(self, event_root=None):
        self.time = time.time()
        self.event_root = event_root
        self.complete = False
        
    def __unicode__(self):
        if self.complete:
           complete = "(completed)"
        else:
           complete = ""
        return u"<WatchEvent: %s %s %s>" % (time.ctime(self.time), self.event_root, complete)

class Handler(pyinotify.ProcessEvent):
    def __init__(self, watchmanager, bot, completion_files=None):
        """
        Completion file contains current "completion" filename
        """
        self.last_event = {}
        self.watchmanager = watchmanager
        self.bot = bot
        if completion_files is not None:
            completion_files = [ x.lower() for x in completion_files ]
        self.completion_files = completion_files

    def process_IN_CREATE(self, event):
        for wdd in self.bot.wdds:
            for watch_path in self.bot.watchdirs:
                run_already_complete = False
                # I only care about things created inside the watch directory, so
                # the event path needs to be longer than the watch path in addition to
                # starting with the watch_path
                if len(event.path) > len(watch_path) and event.path.startswith(watch_path):
                    # compute name of the top level directory that had an event
                    # in the current watch path
                    target = get_top_dir(watch_path, event.path)
                    runfolder = os.path.join(watch_path, target)

                    if not is_runfolder(target):
                        logging.debug("Skipping %s, not a runfolder" % (target,))
                        continue
                    
                    # grab the previous events for this watch path
                    watch_path_events = self.last_event.setdefault(watch_path, {})

                    # if we've already seen an event in this directory (AKA runfolder)
                    # keep track if its already hit the "completed" flag
                    if watch_path_events.has_key(target):
                       run_already_complete = watch_path_events[target].complete

                    watch_path_events[target] = WatcherEvent(target)
                    #self.last_event.setdefault(watch_path, {})[target] = WatcherEvent(target)

                    msg = "Create: %s %s %s %s" % (watch_path, target, event.path, event.name)

                    # the ReadPrep step uses some of the same file completion flags as the
                    # main analysis, which means this completion code might get tripped because of it
                    # so we need to make sure we're getting the completion file in the root of the
                    # runfolder
                    event_name = event.name.lower()
                    if (event_name in self.completion_files and event.path == runfolder) \
                      or run_already_complete:
                        self.last_event[watch_path][target].complete = True
                        msg += "(completed)"

                    logging.debug(msg)

    def process_IN_DELETE(self, event):
        logging.debug("Remove: %s" %  os.path.join(event.path, event.name))
        pass

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
    #    `completion_files` - what files indicates we've finished sequencing
    #                        defaults to: netcopy_complete.txt
    
    def __init__(self, section=None, configfile=None):
        #if configfile is None:
        #    self.configfile = "~/.htsworkflow"
        super(SpoolWatcher, self).__init__(section, configfile)
        
        self.cfg['watchdirs'] = None
        self.cfg['write_timeout'] = 10
        self.cfg['notify_users'] = None
        self.cfg['notify_runner'] = None
        self.cfg['completion_files'] = 'ImageAnalysis_Netcopy_complete_READ2.txt ImageAnalysis_Netcopy_complete_SINGLEREAD.txt'
       
        self.watchdirs = []
        self.watchdir_url_map = {}
        self.notify_timeout = 0.001

        self.wm = None 
        self.notify_users = None
        self.notify_runner = None
        self.wdds = []

        # keep track if the specified mount point is currently mounted
        self.mounted_points = {}
        # keep track of which mount points tie to which watch directories
        # so maybe we can remount them.
        self.mounts_to_watches = {}
        
        self.eventTasks.append(self.process_notify)

    def read_config(self, section=None, configfile=None):
        # Don't give in to the temptation to use logging functions here, 
        # need to wait until after we detach in start
        super(SpoolWatcher, self).read_config(section, configfile)
        
        self.watchdirs = shlex.split(self._check_required_option('watchdirs'))
        # see if there's an alternate url that should be used for the watchdir
        for watchdir in self.watchdirs:
            self.watchdir_url_map[watchdir] = self.cfg.get(watchdir, watchdir)

        self.write_timeout = int(self.cfg['write_timeout'])
        self.completion_files = shlex.split(self.cfg['completion_files'])
        
        self.notify_users = self._parse_user_list(self.cfg['notify_users'])
        try:
          self.notify_runner = \
             self._parse_user_list(self.cfg['notify_runner'],
                                   require_resource=True)
        except bot.JIDMissingResource:
            msg = 'need a full jabber ID + resource for xml-rpc destinations'
            raise bot.JIDMissingResource(msg)

        self.handler = None
        self.notifier = None

    def add_watch(self, watchdirs=None):
        """
        start watching watchdir or self.watchdir
        we're currently limited to watching one directory tree.
        """
        # create the watch managers if we need them
        if self.wm is None:
            self.wm = pyinotify.WatchManager()
            self.handler = Handler(self.wm, self, self.completion_files)
            self.notifier = pyinotify.Notifier(self.wm, self.handler)

        # the one tree limit is mostly because self.wdd is a single item
        # but managing it as a list might be a bit more annoying
        if watchdirs is None:
            watchdirs = self.watchdirs

        mask = IN_CREATE | IN_UNMOUNT
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

    def make_copy_url(self, watchdir, list_event_dir):
        root_copy_url = self.watchdir_url_map[watchdir]
        if root_copy_url[-1] != '/':
            root_copy_url += '/'
        copy_url = root_copy_url + list_event_dir
        logging.debug('Copy url: %s' % (copy_url,))
        return copy_url
                  
    def process_notify(self, *args):
        if self.notifier is None:
            # nothing to do yet
            return
        # process the queue of events as explained above
        self.notifier.process_events()
        #check events waits timeout
        if self.notifier.check_events(self.notify_timeout):
            # read notified events and enqeue them
            self.notifier.read_events()
            # should we do something?
        # has something happened?
        for watchdir, last_events in self.handler.last_event.items():
            for last_event_dir, last_event_detail in last_events.items():
                time_delta = time.time() - last_event_detail.time
                if time_delta > self.write_timeout:
                    print "timeout", unicode(last_event_detail)
                    copy_url = self.make_copy_url(watchdir, last_event_dir)
                    self.startCopy(copy_url)
                    if last_event_detail.complete:
                        self.sequencingFinished(last_event_detail.event_root)

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
            self.startCopy(msg)
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
        
    def run(self):
        """
        Start application
        """
        # we have to configure pyinotify after BenderJab.start is called
        # as weird things happen to pyinotify if the stdio is closed
        # after it's initialized.
        self.add_watch()
        super(SpoolWatcher, self).run()
        
    def stop(self):
        """
        shutdown application
        """
        # destroy the inotify's instance on this interrupt (stop monitoring)
        if self.notifier is not None:
            self.notifier.stop()
        super(SpoolWatcher, self).stop()
    
    def startCopy(self, copy_url=None):
        logging.debug("writes seem to have stopped")
        if self.notify_runner is not None:
            for r in self.notify_runner:
                self.rpc_send(r, tuple([copy_url]), 'startCopy')
        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, 'startCopy %s.' % (copy_url,))
        
    def sequencingFinished(self, run_dir):
        # need to strip off self.watchdirs from rundir I suspect.
        logging.info("run.completed in " + str(run_dir))
        for watch in self.watchdirs:
            if not run_dir.startswith(watch):
                print "%s didn't start with %s" % (run_dir, watch)
                continue
            if watch[-1] != os.path.sep:
                watch += os.path.sep
            stripped_run_dir = re.sub(watch, "", run_dir)
        else:
            stripped_run_dir = run_dir

        logging.debug("stripped to " + stripped_run_dir)
        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, 'Sequencing run %s finished' % \
                          (stripped_run_dir))
        if self.notify_runner is not None:
            for r in self.notify_runner:
                self.rpc_send(r, (stripped_run_dir,), 'sequencingFinished')

def main(args=None):
    bot = SpoolWatcher()
    return bot.main(args)
    
if __name__ == "__main__":
    ret = main(sys.argv[1:])
    #sys.exit(ret)

# TODO:
# send messages to copier specifying which mount to copy
