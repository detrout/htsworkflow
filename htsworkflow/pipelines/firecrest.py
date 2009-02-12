"""
Extract information about the Firecrest run

Firecrest 
  class holding the properties we found
firecrest 
  Firecrest factory function initalized from a directory name
fromxml 
  Firecrest factory function initalized from an xml dump from
  the Firecrest object.
"""

from datetime import date
import os
import re
import time

from htsworkflow.pipelines.runfolder import \
   ElementTree, \
   VERSION_RE, \
   EUROPEAN_STRPTIME

__docformat__ = "restructuredtext en"

class Firecrest(object):
    XML_VERSION=1

    # xml tag names
    FIRECREST = 'Firecrest'
    SOFTWARE_VERSION = 'version'
    START = 'FirstCycle'
    STOP = 'LastCycle'
    DATE = 'run_time'
    USER = 'user'
    MATRIX = 'matrix'

    def __init__(self, xml=None):
        self.start = None
        self.stop = None
        self.version = None
        self.date = date.today()
        self.user = None
        self.matrix = None

        if xml is not None:
            self.set_elements(xml)
        
    def _get_time(self):
        return time.mktime(self.date.timetuple())
    time = property(_get_time, doc='return run time as seconds since epoch')

    def dump(self):
        print "Starting cycle:", self.start
        print "Ending cycle:", self.stop
        print "Firecrest version:", self.version
        print "Run date:", self.date
        print "user:", self.user

    def get_elements(self):
        attribs = {'version': str(Firecrest.XML_VERSION) }
        root = ElementTree.Element(Firecrest.FIRECREST, attrib=attribs)
        version = ElementTree.SubElement(root, Firecrest.SOFTWARE_VERSION)
        version.text = self.version
        start_cycle = ElementTree.SubElement(root, Firecrest.START)
        start_cycle.text = str(self.start)
        stop_cycle = ElementTree.SubElement(root, Firecrest.STOP)
        stop_cycle.text = str(self.stop)
        run_date = ElementTree.SubElement(root, Firecrest.DATE)
        run_date.text = str(self.time)
        user = ElementTree.SubElement(root, Firecrest.USER)
        user.text = self.user
        matrix = ElementTree.SubElement(root, Firecrest.MATRIX)
        matrix.text = self.matrix
        return root

    def set_elements(self, tree):
        if tree.tag != Firecrest.FIRECREST:
            raise ValueError('Expected "Firecrest" SubElements')
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > Firecrest.XML_VERSION:
            logging.warn('Firecrest XML tree is a higher version than this class')
        for element in list(tree):
            if element.tag == Firecrest.SOFTWARE_VERSION:
                self.version = element.text
            elif element.tag == Firecrest.START:
                self.start = int(element.text)
            elif element.tag == Firecrest.STOP:
                self.stop = int(element.text)
            elif element.tag == Firecrest.DATE:
                self.date = date.fromtimestamp(float(element.text))
            elif element.tag == Firecrest.USER:
                self.user = element.text
            elif element.tag == Firecrest.MATRIX:
                self.matrix = element.text
            else:
                raise ValueError("Unrecognized tag: %s" % (element.tag,))

def firecrest(pathname):
    """
    Examine the directory at pathname and initalize a Firecrest object
    """
    f = Firecrest()

    # parse firecrest directory name
    path, name = os.path.split(pathname)
    groups = name.split('_')
    # grab the start/stop cycle information
    cycle = re.match("C([0-9]+)-([0-9]+)", groups[0])
    f.start = int(cycle.group(1))
    f.stop = int(cycle.group(2))
    # firecrest version
    version = re.search(VERSION_RE, groups[1])
    f.version = (version.group(1))
    # datetime
    t = time.strptime(groups[2], EUROPEAN_STRPTIME)
    f.date = date(*t[0:3])
    # username
    f.user = groups[3]

    # should I parse this deeper than just stashing the 
    # contents of the matrix file?
    matrix_pathname = os.path.join(pathname, 'Matrix', 's_matrix.txt')
    if not os.path.exists(matrix_pathname):
        return None
    f.matrix = open(matrix_pathname, 'r').read()
    return f

def fromxml(tree):
    """
    Initialize a Firecrest object from an element tree node
    """
    f = Firecrest()
    f.set_elements(tree)
    return f
