"""
Extract configuration from Illumina Bustard Directory.

This includes the version number, run date, bustard executable parameters, and
phasing estimates.
"""
from copy import copy
from datetime import date
from glob import glob
import logging
import os
import re
import sys
import time

from htsworkflow.pipelines.runfolder import \
   ElementTree, \
   VERSION_RE, \
   EUROPEAN_STRPTIME

LOGGER = logging.getLogger(__name__)

# make epydoc happy
__docformat__ = "restructuredtext en"

LANE_LIST = range(1,9)

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
        root.tail = os.linesep
        phasing = ElementTree.SubElement(root, Phasing.PHASING)
        phasing.text = str(self.phasing)
        phasing.tail = os.linesep
        prephasing = ElementTree.SubElement(root, Phasing.PREPHASING)
        prephasing.text = str(self.prephasing)
        prephasing.tail = os.linesep
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

class CrosstalkMatrix(object):
    CROSSTALK = "MatrixElements"
    BASE = 'Base'
    ELEMENT = 'Element'

    def __init__(self, fromfile=None, xml=None):
        self.base = {}

        if fromfile is not None:
            self._initialize_from_file(fromfile)
        elif xml is not None:
            self.set_elements(xml)

    def _initialize_from_file(self, pathname):
        data = open(pathname).readlines()
        auto_header = '# Auto-generated frequency response matrix'
        if data[0].strip() == auto_header and len(data) == 9:
            # skip over lines 1,2,3,4 which contain the 4 bases
            self.base['A'] = [ float(v) for v in data[5].split() ]
            self.base['C'] = [ float(v) for v in data[6].split() ]
            self.base['G'] = [ float(v) for v in data[7].split() ]
            self.base['T'] = [ float(v) for v in data[8].split() ]
        elif len(data) == 16:
            self.base['A'] = [ float(v) for v in data[:4] ]
            self.base['C'] = [ float(v) for v in data[4:8] ]
            self.base['G'] = [ float(v) for v in data[8:12] ]
            self.base['T'] = [ float(v) for v in data[12:16] ]
        else:
            raise RuntimeError("matrix file %s is unusual" % (pathname,))
    def get_elements(self):
        root = ElementTree.Element(CrosstalkMatrix.CROSSTALK)
        root.tail = os.linesep
        base_order = ['A','C','G','T']
        for b in base_order:
            base_element = ElementTree.SubElement(root, CrosstalkMatrix.BASE)
            base_element.text = b
            base_element.tail = os.linesep
        for b in base_order:
            for value in self.base[b]:
                crosstalk_value = ElementTree.SubElement(root, CrosstalkMatrix.ELEMENT)
                crosstalk_value.text = unicode(value)
                crosstalk_value.tail = os.linesep

        return root

    def set_elements(self, tree):
        if tree.tag != CrosstalkMatrix.CROSSTALK:
            raise ValueError('Invalid run-xml exptected '+CrosstalkMatrix.CROSSTALK)
        base_order = []
        current_base = None
        current_index = 0
        for element in tree.getchildren():
            # read in the order of the bases
            if element.tag == 'Base':
                base_order.append(element.text)
            elif element.tag == 'Element':
                # we're done reading bases, now its just the 4x4 matrix
                # written out as a list of elements
                # if this is the first element, make a copy of the list
                # to play with and initialize an empty list for the current base
                if current_base is None:
                    current_base = copy(base_order)
                    self.base[current_base[0]] = []
                # we found (probably) 4 bases go to the next base
                if current_index == len(base_order):
                    current_base.pop(0)
                    current_index = 0
                    self.base[current_base[0]] = []
                value = float(element.text)
                self.base[current_base[0]].append(value)

                current_index += 1
            else:
                raise RuntimeError("Unrecognized tag in run xml: %s" %(element.tag,))

def crosstalk_matrix_from_bustard_config(bustard_path, bustard_config_tree):
    """
    Analyze the bustard config file and try to find the crosstalk matrix.
    """
    bustard_run = bustard_config_tree[0]
    if bustard_run.tag != 'Run':
        raise RuntimeError('Expected Run tag, got %s' % (bustard_run.tag,))

    call_parameters = bustard_run.find('BaseCallParameters')
    if call_parameters is None:
        raise RuntimeError('Missing BaseCallParameters section')

    matrix = call_parameters.find('Matrix')
    if matrix is None:
        raise RuntimeError('Expected to find Matrix in Bustard BaseCallParameters')

    matrix_auto_flag = int(matrix.find('AutoFlag').text)
    matrix_auto_lane = int(matrix.find('AutoLane').text)

    crosstalk = None
    if matrix_auto_flag:
        # we estimated the matrix from something in this run.
        # though we don't really care which lane it was
        if matrix_auto_lane == 0:
            # its defaulting to all of the lanes, so just pick one
            auto_lane_fragment = "_1"
        else:
            auto_lane_fragment = "_%d" % ( matrix_auto_lane,)

        for matrix_name in ['s%s_02_matrix.txt' % (auto_lane_fragment,),
                            's%s_1_matrix.txt' % (auto_lane_fragment,),
                            ]:
            matrix_path = os.path.join(bustard_path, 'Matrix', matrix_name)
            if os.path.exists(matrix_path):
                break
        else:
            raise RuntimeError("Couldn't find matrix for lane %d" % \
                               (matrix_auto_lane,))

        crosstalk = CrosstalkMatrix(matrix_path)
    else:
        matrix_elements = call_parameters.find('MatrixElements')
        # the matrix was provided
        if matrix_elements is not None:
            crosstalk = CrosstalkMatrix(xml=matrix_elements)
        else:
            # we have no crosstalk matrix?
            pass

    return crosstalk

class Bustard(object):
    XML_VERSION = 2

    # Xml Tags
    BUSTARD = 'Bustard'
    SOFTWARE_VERSION = 'version'
    DATE = 'run_time'
    USER = 'user'
    PARAMETERS = 'Parameters'
    BUSTARD_CONFIG = 'BaseCallAnalysis'

    def __init__(self, xml=None):
        self._path_version = None # version number from directory name
        self.date = None
        self.user = None
        self.phasing = {}
        self.crosstalk = None
        self.pathname = None
        self.bustard_config = None

        if xml is not None:
            self.set_elements(xml)

    def update_attributes_from_pathname(self):
        """Update version, date, user from bustard directory names
        Obviously this wont work for BaseCalls or later runfolders
        """
        if self.pathname is None:
            raise ValueError(
                "Set pathname before calling update_attributes_from_pathname")
        path, name = os.path.split(self.pathname)

        if not re.match('bustard', name, re.IGNORECASE):
            return

        groups = name.split("_")
        version = re.search(VERSION_RE, groups[0])
        self._path_version = version.group(1)
        t = time.strptime(groups[1], EUROPEAN_STRPTIME)
        self.date = date(*t[0:3])
        self.user = groups[2]

    def _get_software_version(self):
        """return software name, version tuple"""
        if self.bustard_config is None:
            if self._path_version is not None:
                return 'Bustard', self._path_version
            else:
                return None
        software_nodes = self.bustard_config.xpath('Run/Software')
        if len(software_nodes) == 0:
            return None
        elif len(software_nodes) > 1:
            raise RuntimeError("Too many software XML elements for bustard.py")
        else:
            return (software_nodes[0].attrib['Name'],
                    software_nodes[0].attrib['Version'])

    def _get_software(self):
        """Return software name"""
        software_version = self._get_software_version()
        return software_version[0] if software_version is not None else None
    software = property(_get_software)

    def _get_version(self):
        """Return software name"""
        software_version = self._get_software_version()
        return software_version[1] if software_version is not None else None
    version = property(_get_version)


    def _get_time(self):
        if self.date is None:
            return None
        return time.mktime(self.date.timetuple())
    time = property(_get_time, doc='return run time as seconds since epoch')

    def dump(self):
        #print ElementTree.tostring(self.get_elements())
        ElementTree.dump(self.get_elements())

    def get_elements(self):
        root = ElementTree.Element('Bustard',
                                   {'version': str(Bustard.XML_VERSION)})
        version = ElementTree.SubElement(root, Bustard.SOFTWARE_VERSION)
        version.text = self.version
        if self.time is not None:
            run_date = ElementTree.SubElement(root, Bustard.DATE)
            run_date.text = str(self.time)
        if self.user is not None:
            user = ElementTree.SubElement(root, Bustard.USER)
            user.text = self.user
        params = ElementTree.SubElement(root, Bustard.PARAMETERS)

        # add phasing parameters
        for lane in LANE_LIST:
            if self.phasing.has_key(lane):
                params.append(self.phasing[lane].get_elements())

        # add crosstalk matrix if it exists
        if self.crosstalk is not None:
            root.append(self.crosstalk.get_elements())

        # add bustard config if it exists
        if self.bustard_config is not None:
            root.append(self.bustard_config)
        return root

    def set_elements(self, tree):
        if tree.tag != Bustard.BUSTARD:
            raise ValueError('Expected "Bustard" SubElements')
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > Bustard.XML_VERSION:
            LOGGER.warn('Bustard XML tree is a higher version than this class')
        for element in list(tree):
            if element.tag == Bustard.SOFTWARE_VERSION:
                self._path_version = element.text
            elif element.tag == Bustard.DATE:
                self.date = date.fromtimestamp(float(element.text))
            elif element.tag == Bustard.USER:
                self.user = element.text
            elif element.tag == Bustard.PARAMETERS:
                for param in element:
                    p = Phasing(xml=param)
                    self.phasing[p.lane] = p
            elif element.tag == CrosstalkMatrix.CROSSTALK:
                self.crosstalk = CrosstalkMatrix(xml=element)
            elif element.tag == Bustard.BUSTARD_CONFIG:
                self.bustard_config = element
            else:
                raise ValueError("Unrecognized tag: %s" % (element.tag,))

def bustard(pathname):
    """
    Construct a Bustard object by analyzing an Illumina Bustard directory.

    :Parameters:
      - `pathname`: A bustard directory

    :Return:
      Fully initialized Bustard object.
    """
    pathname = os.path.abspath(pathname)
    bustard_filename = os.path.join(pathname, 'config.xml')
    demultiplexed_filename = os.path.join(pathname,
                                          'DemultiplexedBustardConfig.xml')

    if os.path.exists(demultiplexed_filename):
        b = bustard_from_hiseq(pathname, demultiplexed_filename)
    elif os.path.exists(bustard_filename):
        b = bustard_from_ga2(pathname, bustard_filename)
    else:
        b = bustard_from_ga1(pathname)

    return b

def bustard_from_ga1(pathname):
    """Initialize bustard class from ga1 era runfolders.
    """
    path, name = os.path.split(pathname)

    groups = name.split("_")
    if len(groups) < 3:
        msg = "Not enough information to create attributes"\
              " from directory name: %s"
        LOGGER.error(msg % (self.pathname,))
        return None

    b = Bustard()
    b.pathname = pathname
    b.update_attributes_from_pathname()
    version = re.search(VERSION_RE, groups[0])
    b._path_version = version.group(1)
    t = time.strptime(groups[1], EUROPEAN_STRPTIME)
    b.date = date(*t[0:3])
    b.user = groups[2]

    # I only found these in Bustard1.9.5/1.9.6 directories
    if b.version in ('1.9.5', '1.9.6'):
        # at least for our runfolders for 1.9.5 and 1.9.6 matrix[1-8].txt are always the same
        crosstalk_file = os.path.join(pathname, "matrix1.txt")
        b.crosstalk = CrosstalkMatrix(crosstalk_file)

    add_phasing(b)
    return b


def bustard_from_ga2(pathname, config_filename):
    """Initialize bustard class from ga2-era runfolder
    Actually I don't quite remember if it is exactly the GA2s, but
    its after the original runfolder style and before the HiSeq.
    """
    # for version 1.3.2 of the pipeline the bustard version number went down
    # to match the rest of the pipeline. However there's now a nifty
    # new (useful) bustard config file.

    # stub values
    b = Bustard()
    b.pathname = pathname
    b.update_attributes_from_pathname()
    bustard_config_root = ElementTree.parse(config_filename)
    b.bustard_config = bustard_config_root.getroot()
    b.crosstalk = crosstalk_matrix_from_bustard_config(b.pathname,
                                                       b.bustard_config)
    add_phasing(b)

    return b

def bustard_from_hiseq(pathname, config_filename):
    b = Bustard()
    b.pathname = pathname
    bustard_config_root = ElementTree.parse(config_filename)
    b.bustard_config = bustard_config_root.getroot()
    add_phasing(b)
    return b

def add_phasing(bustard_obj):
    paramfiles = glob(os.path.join(bustard_obj.pathname,
                                   "params?.xml"))
    for paramfile in paramfiles:
        phasing = Phasing(paramfile)
        assert (phasing.lane >= 1 and phasing.lane <= 8)
        bustard_obj.phasing[phasing.lane] = phasing

def fromxml(tree):
    """
    Reconstruct a htsworkflow.pipelines.Bustard object from an xml block
    """
    b = Bustard()
    b.set_elements(tree)
    return b

def make_cmdline_parser():
    from optparse import OptionParser
    parser = OptionParser('%prog: bustard_directory')
    return parser

def main(cmdline):
    parser = make_cmdline_parser()
    opts, args = parser.parse_args(cmdline)

    for bustard_dir in args:
        print u'analyzing bustard directory: ' + unicode(bustard_dir)
        bustard_object = bustard(bustard_dir)
        bustard_object.dump()

        bustard_object2 = Bustard(xml=bustard_object.get_elements())
        print ('-------------------------------------')
        bustard_object2.dump()
        print ('=====================================')
        b1_tree = bustard_object.get_elements()
        b1 = ElementTree.tostring(b1_tree).split(os.linesep)
        b2_tree = bustard_object2.get_elements()
        b2 = ElementTree.tostring(b2_tree).split(os.linesep)
        for line1, line2 in zip(b1, b2):
            if b1 != b2:
                print "b1: ", b1
                print "b2: ", b2

if __name__ == "__main__":
    main(sys.argv[1:])
