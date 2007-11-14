#!/usr/bin/python
import subprocess
import re
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='config_pipeline.log',
                    filemode='w')

#Info
s_start = re.compile('Starting Genome Analyzer Pipeline')
s_gerald = re.compile("[\S\s]+--GERALD[\S\s]+--make[\S\s]+")
s_generating = re.compile('Generating journals, Makefiles and parameter files')

#Errors
s_invalid_cmdline = re.compile('Usage:[\S\s]*goat_pipeline.py')

#Ignore
s_skip = re.compile('s_[0-8]_[0-9]+')

def handler(line):

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
  else:
    logging.warning('How to handle: %s' % (line))
  

def configure():
  #ERROR Test:
  #pipe = subprocess.Popen(['goat_pipeline.py',
  #                         '--GERALD=config32bk.txt',
  #                         '--make .',],
  #                         #'.'],
  #                        stdout=subprocess.PIPE,
  #                        stderr=subprocess.PIPE)

  #Not a test; actual run attempt.
  pipe = subprocess.Popen(['goat_pipeline.py',
                           '--GERALD=config32bk.txt',
                           '--make',
                           '.'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  
  line = pipe.stdout.readline()

  while line != '':
    handler(line)
    line = pipe.stdout.readline()

  #print pipe.poll()


if __name__ == '__main__':
  configure()
