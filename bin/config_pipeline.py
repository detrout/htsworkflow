#!/usr/bin/python
import subprocess
import re
import os
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='config_pipeline.log',
                    filemode='w')

class ConfigInfo:
  
  def __init__(self):
    self.run_path = None
    self.bustard_path = None
    self.config_filepath = None

#FLAGS
RUN_ABORT = 'abort'

#Info
s_start = re.compile('Starting Genome Analyzer Pipeline')
s_gerald = re.compile("[\S\s]+--GERALD[\S\s]+--make[\S\s]+")
s_generating = re.compile('Generating journals, Makefiles and parameter files')
s_seq_folder = re.compile('^Sequence folder: ')
s_stderr_taskcomplete = re.compile('^Task complete, exiting')

#Errors
s_invalid_cmdline = re.compile('Usage:[\S\s]*goat_pipeline.py')
s_species_dir_err = re.compile('Error: Lane [1-8]:')

#Ignore
s_skip = re.compile('s_[0-8]_[0-9]+')

def config_stdout_handler(line, conf_info):
  """
  Processes each line of output from GOAT
  and stores useful information using the logging module

  Loads useful information into conf_info as well, for future
  use outside the function.

  returns True if found condition that signifies success.
  """

  # Irrelevant line
  if s_skip.search(line):
    pass
  elif s_invalid_cmdline.search(line):
    logging.error("Invalid commandline options!")
  elif s_start.search(line):
    logging.info('START: Configuring pipeline')
  elif s_gerald.search(line):
    logging.info('Running make now')
  elif s_generating.search(line):
    logging.info('Make files generted')
    return True
  elif s_seq_folder.search(line):
    mo = s_seq_folder.search(line)
    conf_info.bustard_path = line[mo.end():]
    conf_info.run_path, temp = os.path.split(conf_info.bustard_path)
  else:
    logging.warning('How to handle: %s' % (line))

  return False



def config_stderr_handler(line, conf_info):
  """
  Processes each line of output from GOAT
  and stores useful information using the logging module

  Loads useful information into conf_info as well, for future
  use outside the function.

  returns RUN_ABORT upon detecting failure; True on success message
  """

  if s_species_dir_err.search(line):
    logging.error(line)
    return RUN_ABORT
  elif s_stderr_taskcomplete.search(line):
    logging.info('Configure step successful (from: stderr)')
    return True
  else:
    logging.debug('STDERR: How to handle: %s' % (line))

  return False

#FIXME: Temperary hack
f = open('pipeline_run.log', 'w')

def pipeline_handler(line, conf_info):
  """
  Processes each line of output from running the pipeline
  and stores useful information using the logging module

  Loads useful information into conf_info as well, for future
  use outside the function.

  returns True if found condition that signifies success.
  """

  f.write(line + '\n')

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

  #Not a test; actual run attempt.
  pipe = subprocess.Popen(['goat_pipeline.py',
                    '--GERALD=%s' % (conf_info.config_filepath),
                           '--make',
                           '.'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

  #Process stdout
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
    logging.info ('We are go for launch!')

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

  # Fail if the run_path doesn't actually exist
  if not os.path.exists(conf_info.run_path):
    logging.error('Run path does not exist: %s' \
              % (conf_info.run_path))
    return False

  # Change cwd to run_path
  os.chdir(conf_info.run_path)

  # Start the pipeline (and hide!)
  pipe = subprocess.Popen(['make',
                           '-j8',
                           'recursive'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

  line = pipe.stdout.readline()

  complete = False
  while line != '':
    if pipeline_handler(line, conf_info):
      complete = True
    line = pipe.stdout.readline()




if __name__ == '__main__':
  ci = ConfigInfo()
  ci.config_filepath = 'config32bk.txt'
  
  status = configure(ci)
  if status:
    print "Configure success"
  else:
    print "Configure failed"

  #print 'Run Dir:', ci.run_path
  #print 'Bustard Dir:', ci.bustard_path

  #if status:
  #  run_pipeline(ci)

  #FIXME: Temperary hack
  f.close()
