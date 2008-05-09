
from datetime import datetime
from glob import glob
import logging
import os
import time
import re

from gaworkflow.pipeline.runfolder import \
   ElementTree, \
   VERSION_RE, \
   EUROPEAN_STRPTIME

class Phasing(object):
    PHASING = 'Phasing'
    PREPHASING = 'Prephasing'

    def __init__(self, fromfile=None, xml=None):
        self.lane = None
        self.phasing = None
        self.prephasing = None

        if fromfile is not None:
            self._initialize_from_file(fromfile)
        elif xml is not None:
            self.set_elements(xml)

    def _initialize_from_file(self, pathname):
        path, name = os.path.split(pathname)
        basename, ext = os.path.splitext(name)
        # the last character of the param base filename should be the
        # lane number
        tree = ElementTree.parse(pathname).getroot()
        self.set_elements(tree)
        self.lane = int(basename[-1])

    def get_elements(self):
        root = ElementTree.Element(Phasing.PHASING, {'lane': str(self.lane)})
        phasing = ElementTree.SubElement(root, Phasing.PHASING)
        phasing.text = str(self.phasing)
        prephasing = ElementTree.SubElement(root, Phasing.PREPHASING)
        prephasing.text = str(self.prephasing)
        return root

    def set_elements(self, tree):
        if tree.tag not in ('Phasing', 'Parameters'):
            raise ValueError('exptected Phasing or Parameters')
        lane = tree.attrib.get('lane', None)
        if lane is not None:
            self.lane = int(lane)
        for element in list(tree):
            if element.tag == Phasing.PHASING:
                self.phasing = float(element.text)
            elif element.tag == Phasing.PREPHASING:
                self.prephasing = float(element.text)

class Bustard(object):
    XML_VERSION = 1

    # Xml Tags
    BUSTARD = 'Bustard'
    SOFTWARE_VERSION = 'version'
    DATE = 'run_time'
    USER = 'user'
    PARAMETERS = 'Parameters'

    def __init__(self, xml=None):
        self.version = None
        self.date = datetime.now()
        self.user = None
        self.phasing = {}

        if xml is not None:
            self.set_elements(xml)

    def _get_time(self):
        return time.mktime(self.date.timetuple())
    time = property(_get_time, doc='return run time as seconds since epoch')

    def dump(self):
        print "Bustard version:", self.version
        print "Run date", self.date
        print "user:", self.user
        for lane, tree in self.phasing.items():
            print lane
            print tree

    def get_elements(self):
        root = ElementTree.Element('Bustard', 
                                   {'version': str(Bustard.XML_VERSION)})
        version = ElementTree.SubElement(root, Bustard.SOFTWARE_VERSION)
        version.text = self.version
        run_date = ElementTree.SubElement(root, Bustard.DATE)
        run_date.text = str(self.time)
        user = ElementTree.SubElement(root, Bustard.USER)
        user.text = self.user
        params = ElementTree.SubElement(root, Bustard.PARAMETERS)
        for p in self.phasing.values():
            params.append(p.get_elements())
        return root

    def set_elements(self, tree):
        if tree.tag != Bustard.BUSTARD:
            raise ValueError('Expected "Bustard" SubElements')
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > Bustard.XML_VERSION:
            logging.warn('Bustard XML tree is a higher version than this class')
        for element in list(tree):
            if element.tag == Bustard.SOFTWARE_VERSION:
                self.version = element.text
            elif element.tag == Bustard.DATE:
                self.date = datetime.fromtimestamp(float(element.text))
            elif element.tag == Bustard.USER:
                self.user = element.text
            elif element.tag == Bustard.PARAMETERS:
                for param in element:
                    p = Phasing(xml=param)
                    self.phasing[p.lane] = p
            else:
                raise ValueError("Unrecognized tag: %s" % (element.tag,))
        


def bustard(pathname):
    """
    Construct a Bustard object from pathname
    """
    b = Bustard()
    path, name = os.path.split(pathname)
    groups = name.split("_")
    version = re.search(VERSION_RE, groups[0])
    b.version = version.group(1)
    b.date = datetime.strptime(groups[1], EUROPEAN_STRPTIME)
    b.user = groups[2]
    paramfiles = glob(os.path.join(pathname, "params?.xml"))
    for paramfile in paramfiles:
        phasing = Phasing(paramfile)
        assert (phasing.lane >= 1 and phasing.lane <= 8)
        b.phasing[phasing.lane] = phasing
    return b

def fromxml(tree):
    b = Bustard()
    b.set_elements(tree)
    return b
