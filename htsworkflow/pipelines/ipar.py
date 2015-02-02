"""
Extract information about the IPAR run

IPAR
    class holding the properties we found
ipar
    IPAR factory function initalized from a directory name
fromxml
    IPAR factory function initalized from an xml dump from
    the IPAR object.
"""
from __future__ import print_function

__docformat__ = "restructuredtext en"

import datetime
from glob import glob
import logging
import os
import re
import stat
import time

from htsworkflow.pipelines import \
   ElementTree, \
   VERSION_RE, \
   EUROPEAN_STRPTIME

LOGGER = logging.getLogger(__name__)
SOFTWARE_NAMES = ('IPAR_1.01', 'IPAR_1.3', 'Intensities')

class Tiles(object):
  def __init__(self, tree):
    self.tree = tree.find("TileSelection")

  def keys(self):
    key_list = []
    for c in self.tree.getchildren():
      k = c.attrib.get('Index', None)
      if k is not None:
        key_list.append(k)
    return key_list

  def values(self):
    value_list = []
    for lane in self.tree.getchildren():
      attributes = {}
      for child in lane.getchildren():
        if child.tag == "Sample":
          attributes['Sample'] = child.text
        elif child.tag == 'TileRange':
          attributes['TileRange'] = (int(child.attrib['Min']),int(child.attrib['Max']))
      value_list.append(attributes)
    return value_list

  def items(self):
    return zip(self.keys(), self.values())

  def __getitem__(self, key):
    # FIXME: this is inefficient. building the dictionary be rescanning the xml.
    v = dict(self.items())
    return v[key]

class IPAR(object):
    XML_VERSION=1

    # xml tag names
    IPAR = 'IPAR'
    TIMESTAMP = 'timestamp'
    MATRIX = 'matrix'
    RUN = 'Run'

    def __init__(self, xml=None):
        self.tree = None
        self.date = datetime.datetime.today()
        self._tiles = None
        if xml is not None:
            self.set_elements(xml)

    def _get_runfolder_name(self):
        """Return runfolder name"""
        if self.tree is None:
            raise ValueError("Can't query an empty run")
        runfolder = self.tree.xpath('RunParameters/RunFolder')
        if len(runfolder) == 0:
            return None
        elif len(runfolder) > 1:
            raise RuntimeError("RunXml parse error looking for RunFolder")
        else:
            return runfolder[0].text
    runfolder_name = property(_get_runfolder_name)

    def _get_software(self):
        """Return software name"""
        if self.tree is None:
            raise ValueError("Can't determine software name, please load a run")
        software = self.tree.xpath('Software')
        if len(software) == 0:
          return None
        elif len(software) > 1:
            raise RuntimeError("Too many software tags, please update ipar.py")
        else:
            return software[0].attrib['Name']
    software = property(_get_software)

    def _get_time(self):
        return time.mktime(self.date.timetuple())
    def _set_time(self, value):
        mtime_tuple = time.localtime(value)
        self.date = datetime.datetime(*(mtime_tuple[0:7]))
    time = property(_get_time, _set_time,
                    doc='run time as seconds since epoch')

    def _get_cycles(self):
        if self.tree is None:
          raise RuntimeError("get cycles called before xml tree initalized")
        cycles = self.tree.find("Cycles")
        assert cycles is not None
        if cycles is None:
          return None
        return cycles.attrib

    def _get_start(self):
        """
        return cycle start
        """
        cycles = self._get_cycles()
        if cycles is not None:
          return int(cycles['First'])
        else:
          return None
    start = property(_get_start, doc="get cycle start")

    def _get_stop(self):
        """
        return cycle stop
        """
        cycles = self._get_cycles()
        if cycles is not None:
          return int(cycles['Last'])
        else:
          return None
    stop = property(_get_stop, doc="get cycle stop")

    def _get_tiles(self):
      if self._tiles is None:
        self._tiles = Tiles(self.tree)
      return self._tiles
    tiles = property(_get_tiles)

    def _get_version(self):
      software = self.tree.find('Software')
      if software is not None:
        return software.attrib['Version']
    version = property(_get_version, "IPAR software version")


    def file_list(self):
        """
        Generate list of all files that should be generated by the IPAR unit
        """
        suffix_node = self.tree.find('RunParameters/CompressionSuffix')
        if suffix_node is None:
          print("find compression suffix failed")
          return None
        suffix = suffix_node.text
        files = []
        format = "%s_%s_%04d_%s.txt%s"
        for lane, attrib in self.tiles.items():
          for file_type in ["int","nse"]:
            start, stop = attrib['TileRange']
            for tile in range(start, stop+1):
              files.append(format % (attrib['Sample'], lane, tile, file_type, suffix))
        return files

    def dump(self):
        print("Matrix:", self.matrix)
        print("Tree:", self.tree)

    def get_elements(self):
        attribs = {'version': str(IPAR.XML_VERSION) }
        root = ElementTree.Element(IPAR.IPAR, attrib=attribs)
        timestamp = ElementTree.SubElement(root, IPAR.TIMESTAMP)
        timestamp.text = str(int(self.time))
        root.append(self.tree)
        matrix = ElementTree.SubElement(root, IPAR.MATRIX)
        matrix.text = self.matrix
        return root

    def set_elements(self, tree):
        if tree.tag != IPAR.IPAR:
            raise ValueError('Expected "IPAR" SubElements')
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > IPAR.XML_VERSION:
            LOGGER.warn('IPAR XML tree is a higher version than this class')
        for element in list(tree):
            if element.tag == IPAR.RUN:
                self.tree = element
            elif element.tag == IPAR.TIMESTAMP:
                self.time = int(element.text)
            elif element.tag == IPAR.MATRIX:
                self.matrix = element.text
            else:
                raise ValueError("Unrecognized tag: %s" % (element.tag,))

def load_ipar_param_tree(paramfile):
    """
    look for a .param file and load it if it is an IPAR tree
    """

    tree = ElementTree.parse(paramfile).getroot()
    run = tree.find('Run')
    if run.attrib.get('Name', None) in SOFTWARE_NAMES:
        return run
    else:
        LOGGER.info("No run found")
        return None

def ipar(pathname):
    """
    Examine the directory at pathname and initalize a IPAR object
    """
    LOGGER.info("Searching IPAR directory %s" % (pathname,))
    i = IPAR()
    i.pathname = pathname

    # parse firecrest directory name
    path, name = os.path.split(pathname)
    groups = name.split('_')
    if not (groups[0] == 'IPAR' or groups[0] == 'Intensities'):
      raise ValueError('ipar can only process IPAR directories')

    # contents of the matrix file?
    matrix_pathname = os.path.join(pathname, 'Matrix', 's_matrix.txt')
    if os.path.exists(matrix_pathname):
        # this is IPAR_1.01
        i.matrix = open(matrix_pathname, 'r').read()
    else:
        i.matrix = None
        # its still live.

    # look for parameter xml file
    paramfiles = [os.path.join(pathname, 'RTAConfig.xml'),
                  os.path.join(pathname, 'config.xml'),
                  os.path.join(path, '.params')]
    for paramfile in paramfiles:
        if os.path.exists(paramfile):
            LOGGER.info("Found IPAR Config file at: %s" % ( paramfile, ))
            i.tree = load_ipar_param_tree(paramfile)
            mtime_local = os.stat(paramfile)[stat.ST_MTIME]
            i.time = mtime_local
            return i

    return i

def fromxml(tree):
    """
    Initialize a IPAR object from an element tree node
    """
    f = IPAR()
    f.set_elements(tree)
    return f
