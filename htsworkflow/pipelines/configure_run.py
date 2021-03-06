#!/usr/bin/python
from __future__ import print_function

__docformat__ = "restructuredtext en"

import subprocess
import logging
import time
import re
import os

from htsworkflow.pipelines.retrieve_config import \
     CONFIG_SYSTEM, CONFIG_USER, \
     FlowCellNotFound, getCombinedOptions, saveConfigFile, WebError404
from htsworkflow.pipelines.genome_mapper import DuplicateGenome, getAvailableGenomes, constructMapperDict
from htsworkflow.pipelines.run_status import GARunStatus

from pyinotify import WatchManager, ThreadedNotifier
from pyinotify import EventsCodes, ProcessEvent

LOGGER = logging.getLogger(__name__)

class ConfigInfo:

  def __init__(self):
    #run_path = firecrest analysis directory to run analysis from
    self.run_path = None
    self.bustard_path = None
    self.config_filepath = None
    self.status = None

    #top level directory where all analyses are placed
    self.base_analysis_dir = None
    #analysis_dir, top level analysis dir...
    # base_analysis_dir + '/070924_USI-EAS44_0022_FC12150'
    self.analysis_dir = None


  def createStatusObject(self):
    """
    Creates a status object which can be queried for
    status of running the pipeline

    returns True if object created
    returns False if object cannot be created
    """
    if self.config_filepath is None:
      return False

    self.status = GARunStatus(self.config_filepath)
    return True



####################################
# inotify event processor

s_firecrest_finished = re.compile('Firecrest[0-9\._\-A-Za-z]+/finished.txt')
s_bustard_finished = re.compile('Bustard[0-9\._\-A-Za-z]+/finished.txt')
s_gerald_finished = re.compile('GERALD[0-9\._\-A-Za-z]+/finished.txt')

s_gerald_all = re.compile('Firecrest[0-9\._\-A-Za-z]+/Bustard[0-9\._\-A-Za-z]+/GERALD[0-9\._\-A-Za-z]+/')
s_bustard_all = re.compile('Firecrest[0-9\._\-A-Za-z]+/Bustard[0-9\._\-A-Za-z]+/')
s_firecrest_all = re.compile('Firecrest[0-9\._\-A-Za-z]+/')

class RunEvent(ProcessEvent):

  def __init__(self, conf_info):

    self.run_status_dict = {'firecrest': False,
                            'bustard': False,
                            'gerald': False}

    self._ci = conf_info

    ProcessEvent.__init__(self)


  def process_IN_CREATE(self, event):
    fullpath = os.path.join(event.path, event.name)
    if s_finished.search(fullpath):
      LOGGER.info("File Found: %s" % (fullpath))

      if s_firecrest_finished.search(fullpath):
        self.run_status_dict['firecrest'] = True
        self._ci.status.updateFirecrest(event.name)
      elif s_bustard_finished.search(fullpath):
        self.run_status_dict['bustard'] = True
        self._ci.status.updateBustard(event.name)
      elif s_gerald_finished.search(fullpath):
        self.run_status_dict['gerald'] = True
        self._ci.status.updateGerald(event.name)

    #WARNING: The following order is important!!
    # Firecrest regex will catch all gerald, bustard, and firecrest
    # Bustard regex will catch all gerald and bustard
    # Gerald regex will catch all gerald
    # So, order needs to be Gerald, Bustard, Firecrest, or this
    #  won't work properly.
    elif s_gerald_all.search(fullpath):
      self._ci.status.updateGerald(event.name)
    elif s_bustard_all.search(fullpath):
      self._ci.status.updateBustard(event.name)
    elif s_firecrest_all.search(fullpath):
      self._ci.status.updateFirecrest(event.name)

    #print "Create: %s" % (os.path.join(event.path, event.name))

  def process_IN_DELETE(self, event):
    #print "Remove %s" % (os.path.join(event.path, event.name))
    pass




#FLAGS
# Config Step Error
RUN_ABORT = 'abort'
# Run Step Error
RUN_FAILED = 'failed'


#####################################
# Configure Step (goat_pipeline.py)
#Info
s_start = re.compile('Starting Genome Analyzer Pipeline')
s_gerald = re.compile("[\S\s]+--GERALD[\S\s]+--make[\S\s]+")
s_generating = re.compile('^Generating journals, Makefiles')
s_seq_folder = re.compile('^Sequence folder: ')
s_seq_folder_sub = re.compile('want to make ')
s_stderr_taskcomplete = re.compile('^Task complete, exiting')

#Errors
s_invalid_cmdline = re.compile('Usage:[\S\s]*goat_pipeline.py')
s_species_dir_err = re.compile('Error: Lane [1-8]:')
s_goat_traceb = re.compile("^Traceback \(most recent call last\):")
s_missing_cycles = re.compile('^Error: Tile s_[1-8]_[0-9]+: Different number of cycles: [0-9]+ instead of [0-9]+')

SUPPRESS_MISSING_CYCLES = False


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
    LOGGER.error("Invalid commandline options!")

  # Detect starting of configuration
  elif s_start.search(line):
    LOGGER.info('START: Configuring pipeline')

  # Detect it made it past invalid arguments
  elif s_gerald.search(line):
    LOGGER.info('Running make now')

  # Detect that make files have been generated (based on output)
  elif s_generating.search(line):
    LOGGER.info('Make files generted')
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
      print('Sequence line:', line)
      mo = s_seq_folder.search(line)
      conf_info.bustard_path = line[mo.end():]
      conf_info.run_path, temp = os.path.split(conf_info.bustard_path)

  # Log all other output for debugging purposes
  else:
    LOGGER.warning('CONF:?: %s' % (line))

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
  global SUPPRESS_MISSING_CYCLES

  # Detect invalid species directory error
  if s_species_dir_err.search(line):
    LOGGER.error(line)
    return RUN_ABORT
  # Detect goat_pipeline.py traceback
  elif s_goat_traceb.search(line):
    LOGGER.error("Goat config script died, traceback in debug output")
    return RUN_ABORT
  # Detect indication of successful configuration (from stderr; odd, but ok)
  elif s_stderr_taskcomplete.search(line):
    LOGGER.info('Configure step successful (from: stderr)')
    return True
  # Detect missing cycles
  elif s_missing_cycles.search(line):

    # Only display error once
    if not SUPPRESS_MISSING_CYCLES:
      LOGGER.error("Missing cycles detected; Not all cycles copied?")
      LOGGER.debug("CONF:STDERR:MISSING_CYCLES: %s" % (line))
      SUPPRESS_MISSING_CYCLES = True
    return RUN_ABORT

  # Log all other output as debug output
  else:
    LOGGER.debug('CONF:STDERR:?: %s' % (line))

  # Neutral (not failure; nor success)
  return False


#def pipeline_stdout_handler(line, conf_info):
#  """
#  Processes each line of output from running the pipeline
#  and stores useful information using the logging module
#
#  Loads useful information into conf_info as well, for future
#  use outside the function.
#
#  returns True if found condition that signifies success.
#  """
#
#  #f.write(line + '\n')
#
#  return True



def pipeline_stderr_handler(line, conf_info):
  """
  Processes each line of stderr from pipelien run
  and stores useful information using the logging module

  ##FIXME: Future feature (doesn't actually do this yet)
  #Loads useful information into conf_info as well, for future
  #use outside the function.

  returns RUN_FAILED upon detecting failure;
          #True on success message; (no clear success state)
          False if neutral message
            (i.e. doesn't signify failure or success)
  """

  if pl_stderr_ignore(line):
    pass
  elif s_make_error.search(line):
    LOGGER.error("make error detected; run failed")
    return RUN_FAILED
  elif s_no_gnuplot.search(line):
    LOGGER.error("gnuplot not found")
    return RUN_FAILED
  elif s_no_convert.search(line):
    LOGGER.error("imagemagick's convert command not found")
    return RUN_FAILED
  elif s_no_ghostscript.search(line):
    LOGGER.error("ghostscript not found")
    return RUN_FAILED
  else:
    LOGGER.debug('PIPE:STDERR:?: %s' % (line))

  return False


def retrieve_config(conf_info, flowcell, cfg_filepath, genome_dir):
  """
  Gets the config file from server...
  requires config file in:
    /etc/ga_frontend/ga_frontend.conf
   or
    ~/.ga_frontend.conf

  with:
  [config_file_server]
  base_host_url: http://host:port

  return True if successful, False is failure
  """
  options = getCombinedOptions()

  if options.url is None:
    LOGGER.error("%s or %s missing base_host_url option" % \
                  (CONFIG_USER, CONFIG_SYSTEM))
    return False

  try:
    saveConfigFile(flowcell, options.url, cfg_filepath)
    conf_info.config_filepath = cfg_filepath
  except FlowCellNotFound as e:
    LOGGER.error(e)
    return False
  except WebError404 as e:
    LOGGER.error(e)
    return False
  except IOError as e:
    LOGGER.error(e)
    return False
  except Exception as e:
    LOGGER.error(e)
    return False

  f = open(cfg_filepath, 'r')
  data = f.read()
  f.close()

  genome_dict = getAvailableGenomes(genome_dir)
  mapper_dict = constructMapperDict(genome_dict)

  LOGGER.debug(data)

  f = open(cfg_filepath, 'w')
  f.write(data % (mapper_dict))
  f.close()

  return True



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


  stdout_filepath = os.path.join(conf_info.analysis_dir,
                                 "pipeline_configure_stdout.txt")
  stderr_filepath = os.path.join(conf_info.analysis_dir,
                                 "pipeline_configure_stderr.txt")

  fout = open(stdout_filepath, 'w')
  ferr = open(stderr_filepath, 'w')

  pipe = subprocess.Popen(['goat_pipeline.py',
                           '--GERALD=%s' % (conf_info.config_filepath),
                           '--make',
                           conf_info.analysis_dir],
                           stdout=fout,
                           stderr=ferr)

  print("Configuring pipeline: %s" % (time.ctime()))
  error_code = pipe.wait()

  # Clean up
  fout.close()
  ferr.close()


  ##################
  # Process stdout
  fout = open(stdout_filepath, 'r')

  stdout_line = fout.readline()

  complete = False
  while stdout_line != '':
    # Handle stdout
    if config_stdout_handler(stdout_line, conf_info):
      complete = True
    stdout_line = fout.readline()

  fout.close()


  #error_code = pipe.wait()
  if error_code:
    LOGGER.error('Recieved error_code: %s' % (error_code))
  else:
    LOGGER.info('We are go for launch!')

  #Process stderr
  ferr = open(stderr_filepath, 'r')
  stderr_line = ferr.readline()

  abort = 'NO!'
  stderr_success = False
  while stderr_line != '':
    stderr_status = config_stderr_handler(stderr_line, conf_info)
    if stderr_status == RUN_ABORT:
      abort = RUN_ABORT
    elif stderr_status is True:
      stderr_success = True
    stderr_line = ferr.readline()

  ferr.close()


  #Success requirements:
  # 1) The stdout completed without error
  # 2) The program exited with status 0
  # 3) No errors found in stdout
  print('#Expect: True, False, True, True')
  print(complete, bool(error_code), abort != RUN_ABORT, stderr_success is True)
  status = complete is True and \
           bool(error_code) is False and \
           abort != RUN_ABORT and \
           stderr_success is True

  # If everything was successful, but for some reason
  #  we didn't retrieve the path info, log it.
  if status is True:
    if conf_info.bustard_path is None or conf_info.run_path is None:
      LOGGER.error("Failed to retrieve run_path")
      return False

  return status


def run_pipeline(conf_info):
  """
  Run the pipeline and monitor status.
  """
  # Fail if the run_path doesn't actually exist
  if not os.path.exists(conf_info.run_path):
    LOGGER.error('Run path does not exist: %s' \
              % (conf_info.run_path))
    return False

  # Change cwd to run_path
  stdout_filepath = os.path.join(conf_info.analysis_dir, 'pipeline_run_stdout.txt')
  stderr_filepath = os.path.join(conf_info.analysis_dir, 'pipeline_run_stderr.txt')

  # Create status object
  conf_info.createStatusObject()

  # Monitor file creation
  wm = WatchManager()
  mask = EventsCodes.IN_DELETE | EventsCodes.IN_CREATE
  event = RunEvent(conf_info)
  notifier = ThreadedNotifier(wm, event)
  notifier.start()
  wdd = wm.add_watch(conf_info.run_path, mask, rec=True)

  # Log pipeline starting
  LOGGER.info('STARTING PIPELINE @ %s' % (time.ctime()))

  # Start the pipeline (and hide!)
  #pipe = subprocess.Popen(['make',
  #                         '-j8',
  #                         'recursive'],
  #                        stdout=subprocess.PIPE,
  #                        stderr=subprocess.PIPE)

  fout = open(stdout_filepath, 'w')
  ferr = open(stderr_filepath, 'w')

  pipe = subprocess.Popen(['make',
                           '--directory=%s' % (conf_info.run_path),
                           '-j8',
                           'recursive'],
                           stdout=fout,
                           stderr=ferr)
                           #shell=True)
  # Wait for run to finish
  retcode = pipe.wait()


  # Clean up
  notifier.stop()
  fout.close()
  ferr.close()

  # Process stderr
  ferr = open(stderr_filepath, 'r')

  run_failed_stderr = False
  for line in ferr:
    err_status = pipeline_stderr_handler(line, conf_info)
    if err_status == RUN_FAILED:
      run_failed_stderr = True

  ferr.close()

  # Finished file check!
  print('RUN SUCCESS CHECK:')
  for key, value in event.run_status_dict.items():
    print('  %s: %s' % (key, value))

  dstatus = event.run_status_dict

  # Success or failure check
  status = (retcode == 0) and \
           run_failed_stderr is False and \
           dstatus['firecrest'] is True and \
           dstatus['bustard'] is True and \
           dstatus['gerald'] is True

  return status


