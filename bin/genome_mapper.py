#!/usr/bin/python
import glob
import sys
import os

import logging

class DuplicateGenome(Exception): pass


def _has_metainfo(genome_dir):
  metapath = os.path.join(genome_dir, '_metainfo_')
  if os.path.isfile(metapath):
    return True
  else:
    return False

def getAvailableGenomes(genome_base_dir):
  """
  raises IOError (on genome_base_dir not found)
  raises DuplicateGenome on duplicate genomes found.
  
  returns a double dictionary (i.e. d[species][build] = path)
  """

  # Need valid directory
  if not os.path.exists(genome_base_dir):
    msg = "Directory does not exist: %s" % (genome_base_dir)
    raise IOError, msg

  # Find all subdirectories
  filepath_list = glob.glob(os.path.join(genome_base_dir, '*'))
  potential_genome_dirs = \
    [ filepath for filepath in filepath_list if os.path.isdir(filepath)]

  # Get list of metadata files
  genome_dir_list = \
    [ dirpath \
      for dirpath in potential_genome_dirs \
      if _has_metainfo(dirpath) ]

  # Genome double dictionary
  d = {}

  for genome_dir in genome_dir_list:
    line = open(os.path.join(genome_dir, '_metainfo_'), 'r').readline().strip()

    # Get species, build... log and skip on failure
    try:
      species, build = line.split('|')
    except:
      logging.warning('Skipping: Invalid metafile (%s) line: %s' \
                      % (metafile, line))
      continue

    build_dict = d.setdefault(species, {})
    if build in build_dict:
      msg = "Duplicate genome for %s|%s" % (species, build)
      raise DuplicateGenome, msg

    build_dict[build] = genome_dir

  return d
  

def constructMapperDict(genome_dict):
  """
  Creates a dictionary which can map the genome
  in the eland config generator output to a local
  genome path

  ie. 'Homo sapiens|hg18' -> <genome_dir>
  """
  mapper_dict = {}
  for species in genome_dict.keys():
    for build in genome_dict[species]:
      mapper_dict[species+'|'+build] = genome_dict[species][build]

  return mapper_dict


if __name__ == '__main__':

  if len(sys.argv) != 2:
    print 'useage: %s <base_genome_dir>' % (sys.argv[0])
    sys.exit(1)

  d = getAvailableGenomes(sys.argv[1])
  d2 = constructMapperDict(d)

  for k,v in d2.items():
    print '%s: %s' % (k,v)
  
  
