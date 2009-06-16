#!/usr/bin/env python

"""
Build a fake directory tree for testing rsync management code.
"""

import os
import random

def make_random_string(length=8):
  """Make a random string, length characters long
  """
  symbols = "abcdefhijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  name = []
  for i in xrange(length):
    name.append(random.choice(symbols))
  return "".join(name)

def make_file(pathname):
  """Make a file with some random stuff in it
  """
  stream = open(pathname,'w')
  stream.write(make_random_string(16))
  stream.close()

def make_tree(root, depth=3, directories=5, files=10):
  """
  Make a tree of random directories and files

  depth is how many levels of subdirectories
  directories is how many directories each subdirectory should have
  files is how many files to create in each directory
  """
  if not os.path.exists(root):
    os.mkdir(root)

  paths = []
  # make files
  for i in range(files):
    name = make_random_string()
    paths.append(name)
    pathname = os.path.join(root, name)
    make_file(pathname)

  # make subdirectories if we still have some depth to go
  if depth > 0:
    for i in range(directories):
      name = make_random_string()
      # paths.append(name)
      pathname = os.path.join(root, name)
      subpaths = make_tree(pathname, depth-1, directories, files)
      paths.extend([ os.path.join(name, x) for x in subpaths ])

  return paths

def generate_paths(root):
  """Make a list of relative paths like generated by make_tree
  """
  paths = []
  for curdir, subdirs, files in os.walk(root):
    paths.extend([ os.path.join(curdir, f) for f in files ])

  # an inefficient way of getting the correct common prefix
  # (e.g. root might not have a trailing /)
  common_root = os.path.commonprefix(paths)
  common_len = len(common_root)
  return [ p[common_len:] for p in paths ]
    
def compare_tree(root, paths, verbose=False):
  """Make sure the tree matches our relative list of paths
  """
  # what we find when we look
  experimental_set = set(generate_paths(root))
  # what we expect
  theoretical_set = set(paths)
  # true if the difference of the two sets is the empty set
  difference = experimental_set - theoretical_set
  issame = (len(difference) == 0)
  if verbose and not issame:
    print difference
  return issame
