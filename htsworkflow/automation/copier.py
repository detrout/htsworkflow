import ConfigParser
import copy
import logging
import logging.handlers
import os
import re
import shlex
import subprocess
import sys
import time
import traceback
import urlparse

from benderjab import rpc

def runfolder_validate(fname):
    """
    Return True if fname looks like a runfolder name
    """
    if re.match("^[0-9]{6}_[-A-Za-z0-9_]*$", fname):
        return True
    else:
        return False
    
class rsync(object):
  def __init__(self, sources, dest, pwfile):
    self.cmd = ['/usr/bin/rsync', ]
    self.pwfile = os.path.expanduser(pwfile)
    self.cmd.append('--password-file=%s' % (self.pwfile))
    self.source_base_list = [ self._normalize_rsync_source(x) for x in sources]
    self.dest_base = dest
    self.processes = {}
    self.exit_code = None

  def list(self):
    """
    Get a directory listing for all our sources
    """
    logging.debug("searching for entries in: %s" % (self.source_base_list,))
    entries = []
    for source in self.source_base_list:
        logging.debug("Scanning %s" % (source,))
        args = copy.copy(self.cmd)
        args.append(source)

        logging.debug("Rsync cmd:" + " ".join(args))
        short_process = subprocess.Popen(args, stdout=subprocess.PIPE)
        exit_code = short_process.wait()
        stdout = short_process.stdout
        # We made sure source ends in a / earlier
        cur_list = [ source+subdir for subdir in self.list_filter(stdout)]
        entries.extend(cur_list)
    logging.debug(u"Found the following: %s" % (unicode(entries)))
    return entries

  def list_filter(self, lines):
    """
    parse rsync directory listing
    """
    dirs_to_copy = []
    direntries = [ x[0:42].split() + [x[43:-1]] for x in lines ]
    logging.debug(u'direntries: %s' % (unicode(direntries),))
    for permissions, size, filedate, filetime, filename in direntries:
      if permissions[0] == 'd':
        # hey its a directory, the first step to being something we want to 
        # copy
        if re.match("[0-9]{6}", filename):
          # it starts with something that looks like a 6 digit date
          # aka good enough for me
          dirs_to_copy.append(filename)
    return dirs_to_copy

  def create_copy_process(self, urlname):
    args = copy.copy(self.cmd)
    # args.append('--dry-run') # Makes testing easier
    # we want to copy everything
    args.append('-rlt') 
    # from here
    args.append(urlname)
    # to here
    args.append(self.dest_base)
    logging.debug("Rsync cmd:" + " ".join(args))
    return subprocess.Popen(args)
 
  def copy(self, url_list=None):
    """
    copy any interesting looking directories over
    return list of items that we started copying.
    """
    # clean up any lingering non-running processes
    self.poll()

    if url_list is None or len(url_list) == 0: 
	    # what's available to copy?
        dirs_to_copy = self.list()
    else:
        dirs_to_copy = url_list
   
    logging.info("dirs to copy %s" % (dirs_to_copy,))

    # lets start copying
    started = []
    for d in dirs_to_copy:
      process = self.processes.get(d, None)
      
      if process is None:
        # we don't have a process, so make one
        logging.info("rsyncing %s" % (d))
        self.processes[d] = self.create_copy_process(d)
        started.append(d)           
    return started

  def _normalize_rsync_source(self, source):
      """
      Make sure that we have a reasonable looking source
      a source must be a directory/collection.
      """
      # we must be a directory
      if source[-1] != '/':
        source += '/'
      # I suppose we could check to see if we start with rsync:// or something
      return source

  def poll(self):
      """
      check currently running processes to see if they're done
      
      return path roots that have finished.
      """
      for dir_key, proc_value in self.processes.items():
          retcode = proc_value.poll()
          if retcode is None:
              # process hasn't finished yet
              pass
          elif retcode == 0:
              logging.info("finished rsyncing %s, exitcode %d" %( dir_key, retcode))
              del self.processes[dir_key]
          else:
              logging.error("rsync failed for %s, exit code %d" % (dir_key, retcode))
              
  def __len__(self):
      """
      Return how many active rsync processes we currently have
      
      Call poll first to close finished processes.
      """
      return len(self.processes)
  
  def keys(self):
      """
      Return list of current run folder names
      """
      return self.processes.keys()

class CopierBot(rpc.XmlRpcBot):
    def __init__(self, section=None, configfile=None):
        #if configfile is None:
        #    configfile = '~/.htsworkflow'
            
        super(CopierBot, self).__init__(section, configfile)
        
        # options for rsync command
        self.cfg['rsync_password_file'] = None
        self.cfg['rsync_sources'] = None
        self.cfg['rsync_destination'] = None 
        
        # options for reporting we're done 
        self.cfg['notify_users'] = None
        self.cfg['notify_runner'] = None
                            
        self.pending = []
        self.rsync = None
        self.notify_users = None
        self.notify_runner = None
        
        self.register_function(self.startCopy)
        self.register_function(self.sequencingFinished)
        self.eventTasks.append(self.update)
       
    def _init_rsync(self):
        """
        Initalize rsync class

        This is only accessible for test purposes.
        """
        # we can't call any logging function until after start finishes.
        # this got moved to a seperate function from run to help with test code
        if self.rsync is None:
            self.rsync = rsync(self.sources, self.destination, self.password)

    def read_config(self, section=None, configfile=None):
        """
        read the config file
        """
        super(CopierBot, self).read_config(section, configfile)
        
        self.sources = shlex.split(self._check_required_option('rsync_sources'))
        self.password = self._check_required_option('rsync_password_file')
        self.destination = self._check_required_option('rsync_destination')
        
        self.notify_users = self._parse_user_list(self.cfg['notify_users'])
        try:
          self.notify_runner = \
             self._parse_user_list(self.cfg['notify_runner'],
                                   require_resource=True)
        except bot.JIDMissingResource:
            msg = 'need a full jabber ID + resource for xml-rpc destinations'
            print >>sys.stderr, msg
            raise bot.JIDMissingResource(msg)

    def run(self):
        """
        Start application
        """
        self._init_rsync()
        super(CopierBot, self).run()

    def startCopy(self, *args):
        """
        start our copy
        """
        # Note, args comes in over the network, so don't trust it.
        logging.debug("Arguments to startCopy %s" % (unicode(args),))
        copy_urls = []
        for a in args:
            clean_url = self.validate_url(a)
            if clean_url is not None:
                copy_urls.append(clean_url)

        logging.info("Validated urls = %s" % (copy_urls,))
        started = self.rsync.copy(copy_urls)
        logging.info("copying:" + " ".join(started)+".")
        return started
        
    def sequencingFinished(self, runDir, *args):
        """
        The run was finished, if we're done copying, pass the message on        
        """
        # close any open processes
        self.rsync.poll()
        
        # see if we're still copying
        if runfolder_validate(runDir):
            logging.info("recevied sequencing finshed for %s" % (runDir))
            self.pending.append(runDir)
            self.startCopy()
            return "PENDING"
        else:
            errmsg = "received bad runfolder name (%s)" % (runDir)
            logging.warning(errmsg)
            # maybe I should use a different error message
            raise RuntimeError(errmsg)
    
    def reportSequencingFinished(self, runDir):
        """
        Send the sequencingFinished message to the interested parties
        """
        if self.notify_users is not None:
            for u in self.notify_users:
                self.send(u, 'Sequencing run %s finished' % (runDir))
        if self.notify_runner is not None:
            for r in self.notify_runner:
                self.rpc_send(r, (runDir,), 'sequencingFinished')
        logging.info("forwarding sequencingFinshed message for %s" % (runDir))
        
    def update(self, *args):
        """
        Update our current status.
        Report if we've finished copying files.
        """
        self.rsync.poll()
        for p in self.pending:
            if p not in self.rsync.keys():
                self.reportSequencingFinished(p)
                self.pending.remove(p)
        
    def _parser(self, msg, who):
        """
        Parse xmpp chat messages
        """
        help = u"I can [copy], or report current [status]"
        if re.match(u"help", msg):
            reply = help
        elif re.match("copy", msg):            
            started = self.startCopy()
            reply = u"started copying " + ", ".join(started)
        elif re.match(u"status", msg):
            msg = [u"Currently %d rsync processes are running." % (len(self.rsync))]
            for d in self.rsync.keys():
              msg.append(u"  " + d)
            reply = os.linesep.join(msg)
        else:
            reply = u"I didn't understand '%s'" % (unicode(msg))
        return reply

    def validate_url(self, url):
        user_url = urlparse.urlsplit(url)
        user_scheme = user_url[0]
        user_netloc = user_url[1]
        user_path = user_url[2]

        for source in self.sources:
            source_url = urlparse.urlsplit(source)
            source_scheme = source_url[0]
            source_netloc = source_url[1]
            source_path = source_url[2]
            if (user_scheme == source_scheme) and \
               (user_netloc == source_netloc) and \
               (user_path.startswith(source_path)):
               return url
        return None

def main(args=None):
    bot = CopierBot()
    bot.main(args)
    
if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))

