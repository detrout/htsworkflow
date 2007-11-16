#!/usr/bin/python
import subprocess
import logging
import time
import re
import os

from pyinotify import WatchManager, ThreadedNotifier
from pyinotify import EventsCodes, ProcessEvent

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='pipeline_main.log',
                    filemode='w')

class ConfigInfo:
  
  def __init__(self):
    self.run_path = None
    self.bustard_path = None
    self.config_filepath = None


class RunEvent(ProcessEvent):

  def process_IN_CREATE(self, event):
    fullpath = os.path.join(event.path, event.name)
    if s_finished.search(fullpath):
      logging.info("File Found: %s" % (fullpath))
    print "Create: %s" % (os.path.join(event.path, event.name))

  def process_IN_DELETE(self, event):
    print "Remove %s" % (os.path.join(event.path, event.name))

#FLAGS
RUN_ABORT = 'abort'
RUN_FAILED = 'failed'


#####################################
# Configure Step (goat_pipeline.py)
#Info
s_start = re.compile('Starting Genome Analyzer Pipeline')
s_gerald = re.compile("[\S\s]+--GERALD[\S\s]+--make[\S\s]+")
s_generating = re.compile('Generating journals, Makefiles and parameter files')
s_seq_folder = re.compile('^Sequence folder: ')
s_seq_folder_sub = re.compile('want to make ')
s_stderr_taskcomplete = re.compile('^Task complete, exiting')

#Errors
s_invalid_cmdline = re.compile('Usage:[\S\s]*goat_pipeline.py')
s_species_dir_err = re.compile('Error: Lane [1-8]:')
s_goat_traceb = re.compile("^Traceback \(most recent call last\):")


##Ignore - Example of out above each ignore regex.
#NOTE: Commenting out an ignore will cause it to be
# logged as DEBUG with the logging module.
#CF_STDERR_IGNORE_LIST = []
s_skip = re.compile('s_[0-8]_[0-9]+')


##########################################
# Pipeline Run Step (make -j8 recursive)

##Info
s_finished = re.compile('finished')

##Errors
s_make_error = re.compile('^make[\S\s]+Error')
s_no_gnuplot = re.compile('gnuplot: command not found')
s_no_convert = re.compile('^Can\'t exec "convert"')
s_no_ghostscript = re.compile('gs: command not found')

##Ignore - Example of out above each ignore regex.
#NOTE: Commenting out an ignore will cause it to be
# logged as DEBUG with the logging module.
#
PL_STDERR_IGNORE_LIST = []
# Info: PF 11802
PL_STDERR_IGNORE_LIST.append( re.compile('^Info: PF') )
# About to analyse intensity file s_4_0101_sig2.txt
PL_STDERR_IGNORE_LIST.append( re.compile('^About to analyse intensity file') )
# Will send output to standard output
PL_STDERR_IGNORE_LIST.append( re.compile('^Will send output to standard output') )
# Found 31877 clusters
PL_STDERR_IGNORE_LIST.append( re.compile('^Found [0-9]+ clusters') )
# Will use quality criterion ((CHASTITY>=0.6)
PL_STDERR_IGNORE_LIST.append( re.compile('^Will use quality criterion') )
# Quality criterion translated to (($F[5]>=0.6))
PL_STDERR_IGNORE_LIST.append( re.compile('^Quality criterion translated to') )
# opened /woldlab/trog/data1/king/070924_USI-EAS44_0022_FC12150/Data/C1-36_Firecrest1.9.1_14-11-2007_king.4/Bustard1.9.1_14-11-2007_king/s_4_0101_qhg.txt
#  AND
# opened s_4_0103_qhg.txt
PL_STDERR_IGNORE_LIST.append( re.compile('^opened[\S\s]+qhg.txt') )
# 81129 sequences out of 157651 passed filter criteria
PL_STDERR_IGNORE_LIST.append( re.compile('^[0-9]+ sequences out of [0-9]+ passed filter criteria') )


def pl_stderr_ignore(line):
  """
  Searches lines for lines to ignore (i.e. not to log)

  returns True if line should be ignored
  returns False if line should NOT be ignored
  """
  for s in PL_STDERR_IGNORE_LIST:
    if s.search(line):
      return True
  return False


def config_stdout_handler(line, conf_info):
  """
  Processes each line of output from GOAT
  and stores useful information using the logging module

  Loads useful information into conf_info as well, for future
  use outside the function.

  returns True if found condition that signifies success.
  """

  # Skip irrelevant line (without logging)
  if s_skip.search(line):
    pass

  # Detect invalid command-line arguments
  elif s_invalid_cmdline.search(line):
    logging.error("Invalid commandline options!")

  # Detect starting of configuration
  elif s_start.search(line):
    logging.info('START: Configuring pipeline')

  # Detect it made it past invalid arguments
  elif s_gerald.search(line):
    logging.info('Running make now')

  # Detect that make files have been generated (based on output)
  elif s_generating.search(line):
    logging.info('Make files generted')
    return True

  # Capture run directory
  elif s_seq_folder.search(line):
    mo = s_seq_folder_sub.search(line)
    #Output changed when using --tiles=<tiles>
    # at least in pipeline v0.3.0b2
    if mo:
      firecrest_bustard_gerald_makefile = line[mo.end():]
      firecrest_bustard_gerald, junk = \
                                os.path.split(firecrest_bustard_gerald_makefile)
      firecrest_bustard, junk = os.path.split(firecrest_bustard_gerald)
      firecrest, junk = os.path.split(firecrest_bustard)

      conf_info.bustard_path = firecrest_bustard
      conf_info.run_path = firecrest
    
    #Standard output handling
    else:
      print 'Sequence line:', line
      mo = s_seq_folder.search(line)
      conf_info.bustard_path = line[mo.end():]
      conf_info.run_path, temp = os.path.split(conf_info.bustard_path)

  # Log all other output for debugging purposes
  else:
    logging.warning('CONF:?: %s' % (line))

  return False



def config_stderr_handler(line, conf_info):
  """
  Processes each line of output from GOAT
  and stores useful information using the logging module

  Loads useful information into conf_info as well, for future
  use outside the function.

  returns RUN_ABORT upon detecting failure;
          True on success message;
          False if neutral message
            (i.e. doesn't signify failure or success)
  """

  # Detect invalid species directory error
  if s_species_dir_err.search(line):
    logging.error(line)
    return RUN_ABORT
  # Detect goat_pipeline.py traceback
  elif s_goat_traceb.search(line):
    logging.error("Goat config script died, traceback in debug output")
    return RUN_ABORT
  # Detect indication of successful configuration (from stderr; odd, but ok)
  elif s_stderr_taskcomplete.search(line):
    logging.info('Configure step successful (from: stderr)')
    return True
  # Log all other output as debug output
  else:
    logging.debug('CONF:STDERR:?: %s' % (line))

  # Neutral (not failure; nor success)
  return False


#FIXME: Temperary hack
f = open('pipeline_run.log', 'w')
#ferr = open('pipeline_err.log', 'w')



def pipeline_stdout_handler(line, conf_info):
  """
  Processes each line of output from running the pipeline
  and stores useful information using the logging module

  Loads useful information into conf_info as well, for future
  use outside the function.

  returns True if found condition that signifies success.
  """

  f.write(line + '\n')

  return True



def pipeline_stderr_handler(line, conf_info):
  """
  """

  if pl_stderr_ignore(line):
    pass
  elif s_make_error.search(line):
    logging.error("make error detected; run failed")
    return RUN_FAILED
  elif s_no_gnuplot.search(line):
    logging.error("gnuplot not found")
    return RUN_FAILED
  elif s_no_convert.search(line):
    logging.error("imagemagick's convert command not found")
    return RUN_FAILED
  elif s_no_ghostscript.search(line):
    logging.error("ghostscript not found")
    return RUN_FAILED
  else:
    logging.debug('PIPE:STDERR:?: %s' % (line))

  return False


def configure(conf_info):
  """
  Attempts to configure the GA pipeline using goat.

  Uses logging module to store information about status.

  returns True if configuration successful, otherwise False.
  """
  #ERROR Test:
  #pipe = subprocess.Popen(['goat_pipeline.py',
  #                         '--GERALD=config32bk.txt',
  #                         '--make .',],
  #                         #'.'],
  #                        stdout=subprocess.PIPE,
  #                        stderr=subprocess.PIPE)

  #ERROR Test (2), causes goat_pipeline.py traceback
  #pipe = subprocess.Popen(['goat_pipeline.py',
  #                  '--GERALD=%s' % (conf_info.config_filepath),
  #                         '--tiles=s_4_100,s_4_101,s_4_102,s_4_103,s_4_104',
  #                         '--make',
  #                         '.'],
  #                        stdout=subprocess.PIPE,
  #                        stderr=subprocess.PIPE)

  ##########################
  # Run configuration step
  #   Not a test; actual configure attempt.
  #pipe = subprocess.Popen(['goat_pipeline.py',
  #                  '--GERALD=%s' % (conf_info.config_filepath),
  #                         '--make',
  #                         '.'],
  #                        stdout=subprocess.PIPE,
  #                        stderr=subprocess.PIPE)

  # CONTINUE HERE
  #FIXME: this only does a run on 5 tiles on lane 4
  pipe = subprocess.Popen(['goat_pipeline.py',
                    '--GERALD=%s' % (conf_info.config_filepath),
                           '--tiles=s_4_0100,s_4_0101,s_4_0102,s_4_0103,s_4_0104',
                           '--make',
                           '.'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  ##################
  # Process stdout
  stdout_line = pipe.stdout.readline()

  complete = False
  while stdout_line != '':
    # Handle stdout
    if config_stdout_handler(stdout_line, conf_info):
      complete = True
    stdout_line = pipe.stdout.readline()


  error_code = pipe.wait()
  if error_code:
    logging.error('Recieved error_code: %s' % (error_code))
  else:
    logging.info('We are go for launch!')

  #Process stderr
  stderr_line = pipe.stderr.readline()

  abort = 'NO!'
  stderr_success = False
  while stderr_line != '':
    stderr_status = config_stderr_handler(stderr_line, conf_info)
    if stderr_status == RUN_ABORT:
      abort = RUN_ABORT
    elif stderr_status is True:
      stderr_success = True
    stderr_line = pipe.stderr.readline()


  #Success requirements:
  # 1) The stdout completed without error
  # 2) The program exited with status 0
  # 3) No errors found in stdout
  print '#Expect: True, False, True, True'
  print complete, bool(error_code), abort != RUN_ABORT, stderr_success is True
  status = complete is True and \
           bool(error_code) is False and \
           abort != RUN_ABORT and \
           stderr_success is True

  # If everything was successful, but for some reason
  #  we didn't retrieve the path info, log it.
  if status is True:
    if conf_info.bustard_path is None or conf_info.run_path is None:
      logging.error("Failed to retrieve run_path")
      return False
  
  return status


def run_pipeline(conf_info):
  """
  Run the pipeline and monitor status.
  """
  # Fail if the run_path doesn't actually exist
  if not os.path.exists(conf_info.run_path):
    logging.error('Run path does not exist: %s' \
              % (conf_info.run_path))
    return False

  # Change cwd to run_path
  os.chdir(conf_info.run_path)

  # Monitor file creation
  wm = WatchManager()
  mask = EventsCodes.IN_DELETE | EventsCodes.IN_CREATE
  notifier = ThreadedNotifier(wm, RunEvent())
  notifier.start()
  wdd = wm.add_watch(conf_info.run_path, mask, rec=True)

  # Log pipeline starting
  logging.info('STARTING PIPELINE @ %s' % (time.ctime()))
  
  # Start the pipeline (and hide!)
  #pipe = subprocess.Popen(['make',
  #                         '-j8',
  #                         'recursive'],
  #                        stdout=subprocess.PIPE,
  #                        stderr=subprocess.PIPE)

  fout = open('pipeline_run_stdout.txt', 'w')
  ferr = open('pipeline_run_stderr.txt', 'w')

  pipe = subprocess.Popen(['make',
                             '-j8',
                             'recursive'],
                             stdout=fout,
                             stderr=ferr)
                             #shell=True)
  retcode = pipe.wait()

  notifier.stop()

  fout.close()
  ferr.close()

  #print ': %s' % (sts)
    
  status = (retcode == 0)

  return status



if __name__ == '__main__':
  ci = ConfigInfo()
  ci.config_filepath = 'config32bk.txt'
  
  status = configure(ci)
  if status:
    print "Configure success"
  else:
    print "Configure failed"

  print 'Run Dir:', ci.run_path
  print 'Bustard Dir:', ci.bustard_path
  
  if status:
    print 'Running pipeline now!'
    run_status = run_pipeline(ci)
    if run_status is True:
      print 'Pipeline ran successfully.'
    else:
      print 'Pipeline run failed.'

  #FIXME: Temperary hack
  f.close()
