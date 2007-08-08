#!/usr/bin/env python

import os
import re
import sys
import time

# this uses pyinotify
import pyinotify
from pyinotify import EventsCodes

from benderjab.xsend import send

copy_jid = "cellthumper@chaos.caltech.edu"
runner_jid = "diane@ghic.org"
copy_jid = runner_jid
class Handler(pyinotify.ProcessEvent):
    def __init__(self, watchmanager):
      self.last_event_time = None
      self.watchmanager = watchmanager

    def process_IN_CREATE(self, event):
      self.last_event_time = time.time()
      msg = "Create: %s" %  os.path.join(event.path, event.name)
      if event.name == "Run.completed":
        print "Run is done!"
        send(runner_jid, "a run finished, launch it, and swap the drive")
      print msg

    def process_IN_DELETE(self, event):
      print "Remove: %s" %  os.path.join(event.path, event.name)

    def process_IN_UNMOUNT(self, event):
      print "Unmounted ", str(event)

class TreeWriteDoneNotifier:
  """
  Watch a directory and send a message when another process is done writing.

  This monitors a directory tree using inotify (linux specific) and 
  after some files having been written will send a message after <timeout>
  seconds of no file writing.

  (Basically when the solexa machine finishes dumping a round of data
  this'll hopefully send out a message saying hey look theres data available
  """

  def __init__(self, watchdir, write_timeout=10, notify_timeout=5):
     self.watchdirs = []
     self.write_timeout = write_timeout
     self.notify_timeout = int(notify_timeout * 1000)

     self.wm = pyinotify.WatchManager()
     self.handler = Handler(self.wm)
     self.notifier = pyinotify.Notifier(self.wm, self.handler)
     
     self.add_watch(watchdir)

  def add_watch(self, watchdir):
     self.watchdirs.append(watchdir)
     print "Watching:", watchdir
     mask = EventsCodes.IN_CREATE | EventsCodes.IN_UNMOUNT
     # rec traverses the tree and adds all the directories that are there 
     # at the start.
     # auto_add will add in new directories as they are created
     self.wdd = self.wm.add_watch(watchdir, mask, rec=True, auto_add=True)

  def event_loop(self):
    while True:  # loop forever
      try:
        # process the queue of events as explained above
        self.notifier.process_events()
        #check events waits timeout
        if self.notifier.check_events(self.notify_timeout):
          # read notified events and enqeue them
          self.notifier.read_events()
        # should we do something?
	last_event_time = self.handler.last_event_time
	if last_event_time is not None:
	  time_delta = time.time() - last_event_time
	  if time_delta > self.write_timeout:
	    self.copying_paused()
	    self.handler.last_event_time = None

      except KeyboardInterrupt:
        # destroy the inotify's instance on this interrupt (stop monitoring)
        self.notifier.stop()
        break

  def copying_paused(self):
    print "more than 10 seconds have elapsed"
    send(copy_jid, "start copy")


if __name__ == "__main__":
  #watcher = TreeWriteDoneNotifier("/tmp")
  watcher = TreeWriteDoneNotifier("/gec/jumpgate/ext0")
  watcher.event_loop()

