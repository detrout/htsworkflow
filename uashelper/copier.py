import copy
import os
import re
import subprocess
import time

class rsync(object):
 
  def __init__(self, pwfile):
    self.pwfile = pwfile
    self.cmd = ['/usr/bin/rsync', '--dry-run', '-a', ]
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

    short_process = subprocess.Popen(args, stdout=subprocess.PIPE)
    direntries = [ x.split() for x in short_process.stdout ]
    for permissions, size, filedate, filetime, filename in direntries:
      #print permissions, filename
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
    args.append(os.path.join(self.source_base, dirname))
    args.append(self.dest_base)
    return subprocess.Popen(args)
 
  def copy(self):
    """copy any interesting looking directories over
    """
    dirs_to_copy = self.list()
    for d in dirs_to_copy:
      process = self.processes.get(d, None)
      if process is None:
        # we don't have a process, so make one
        print "starting rsync", d
        self.processes[d] = self.create_copy_process(d)
      else:
        retcode = process.poll()
        if retcode is not None:
           # we finished
           print "rsync",d,"exited with state", retcode
           del self.processes[d]

if __name__ == "__main__":
  r = rsync('/home/diane/.sequencer')
  r.copy()
  while len(r.processes) > 0:
    print "call..."
    r.copy()
    #time.sleep(0.1)
