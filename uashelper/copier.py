import copy
import logging
import logging.handlers
import os
import re
import subprocess
import sys
import time
import traceback

from benderjab.bot import BenderFactory

class rsync(object):
 
  def __init__(self, pwfile):
    self.pwfile = pwfile
    self.cmd = ['/usr/bin/rsync', ]
    self.cmd.append('--password-file=%s' % (pwfile))
    self.source_base = 'rsync://sequencer@jumpgate.caltech.edu:8730/sequencer/'
    self.dest_base = '/home/diane/gec/'
    self.processes = {}
    self.exit_code = None

  def list(self):
    """Get a directory listing"""
    dirs_to_copy = []
    args = copy.copy(self.cmd)
    args.append(self.source_base)

    logging.debug("Rsync cmd:" + " ".join(args))
    short_process = subprocess.Popen(args, stdout=subprocess.PIPE)
    direntries = [ x.split() for x in short_process.stdout ]
    for permissions, size, filedate, filetime, filename in direntries:
      if permissions[0] == 'd':
        # hey its a directory, the first step to being something we want to 
        # copy
        if re.match("[0-9]{6}", filename):
          # it starts with something that looks like a 6 digit date
          # aka good enough for me
          dirs_to_copy.append(filename)
    return dirs_to_copy

  def create_copy_process(self, dirname):
    args = copy.copy(self.cmd)
    # we want to copy everything
    args.append('-rlt') 
    # from here
    args.append(os.path.join(self.source_base, dirname))
    # to here
    args.append(self.dest_base)
    logging.debug("Rsync cmd:" + " ".join(args))
    return subprocess.Popen(args)
 
  def copy(self):
    """copy any interesting looking directories over
    """
    dirs_to_copy = self.list()
    for d in dirs_to_copy:
      process = self.processes.get(d, None)
      if process is None:
        # we don't have a process, so make one
        logging.info("rsyncing %s" % (d))
        self.processes[d] = self.create_copy_process(d)
      else:
        retcode = process.poll()
        if retcode is not None:
           # we finished
           logging.info("finished rsyncing %s, exitcode %d" % (d, retcode))
           del self.processes[d]

class copier_bot_parser(object):
  def __init__(self, ):
    self.rsync = rsync('/home/diane/.sequencer')
  
  def __call__(self, msg, who):
    try:
      if re.match("start copy", msg):
        logging.info("starting copy for %s" % (who.getStripped()))
        self.rsync.copy()
    except Exception, e:
      errmsg = "Exception: " + str(e)
      logging.error(errmsg)
      logging.error(traceback.format_exc())
      return errmsg

def main(args=None):
  if len(args) != 1:
    print "need .benderjab config name"
  configname = args[0]

  logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s %(levelname)s %(message)s')
  log = logging.getLogger()
  log.addHandler(logging.handlers.RotatingFileHandler(
                   '/tmp/copier_bot.log', maxBytes=1000000, backupCount = 3)
                )
  bot = BenderFactory(configname)
  bot.parser = copier_bot_parser()
  bot.logon()
  bot.eventLoop()
  logging.shutdown()
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))

