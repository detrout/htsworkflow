"""
Provide access to information stored in the GERALD directory.
"""
from datetime import datetime, date
import logging
import os
import stat
import time

from htsworkflow.pipelines.summary import Summary
from htsworkflow.pipelines.eland import eland, ELAND

from htsworkflow.pipelines.runfolder import \
   ElementTree, \
   EUROPEAN_STRPTIME, \
   LANES_PER_FLOWCELL, \
   VERSION_RE
from htsworkflow.util.ethelp import indent, flatten

LOGGER = logging.getLogger(__name__)

class Gerald(object):
    """
    Capture meaning out of the GERALD directory
    """
    XML_VERSION = 1
    GERALD='Gerald'
    RUN_PARAMETERS='RunParameters'
    SUMMARY='Summary'

    class LaneParameters(object):
        """
        Make it easy to access elements of LaneSpecificRunParameters from python
        """
        def __init__(self, gerald, lane_id):
            self._gerald = gerald
            self._lane_id = lane_id

        def __get_attribute(self, xml_tag):
            subtree = self._gerald.tree.find('LaneSpecificRunParameters')
            container = subtree.find(xml_tag)
            if container is None:
                return None
            if len(container.getchildren()) > LANES_PER_FLOWCELL:
                raise RuntimeError('GERALD config.xml file changed')
            lanes = [x.tag.split('_')[1] for x in container.getchildren()]
            try:
                index = lanes.index(self._lane_id)
            except ValueError, e:
                return None
            element = container[index]
            return element.text
        def _get_analysis(self):
            return self.__get_attribute('ANALYSIS')
        analysis = property(_get_analysis)

        def _get_eland_genome(self):
            genome = self.__get_attribute('ELAND_GENOME')
            # default to the chipwide parameters if there isn't an
            # entry in the lane specific paramaters
            if genome is None:
                genome = self._gerald._get_chip_attribute('ELAND_GENOME')
            # ignore flag value
            if genome == 'Need_to_specify_ELAND_genome_directory':
                genome = None
            return genome
        eland_genome = property(_get_eland_genome)

        def _get_read_length(self):
            read_length = self.__get_attribute('READ_LENGTH')
            if read_length is None:
                read_length = self._gerald._get_chip_attribute('READ_LENGTH')
            return read_length
        read_length = property(_get_read_length)

        def _get_use_bases(self):
            return self.__get_attribute('USE_BASES')
        use_bases = property(_get_use_bases)

    class LaneSpecificRunParameters(object):
        """
        Provide access to LaneSpecificRunParameters
        """
        def __init__(self, gerald):
            self._gerald = gerald
            self._lane = None

        def _initalize_lanes(self):
            """
            build dictionary of LaneParameters
            """
            self._lanes = {}
            tree = self._gerald.tree
            analysis = tree.find('LaneSpecificRunParameters/ANALYSIS')
            if analysis is None:
                return
            # according to the pipeline specs I think their fields
            # are sampleName_laneID, with sampleName defaulting to s
            # since laneIDs are constant lets just try using
            # those consistently.
            for element in analysis:
                sample, lane_id = element.tag.split('_')
                self._lanes[int(lane_id)] = Gerald.LaneParameters(
                                              self._gerald, lane_id)

        def __getitem__(self, key):
            if self._lane is None:
                self._initalize_lanes()
            return self._lanes[key]
        def get(self, key, default):
            if self._lane is None:
                self._initalize_lanes()
            return self._lanes.get(key, None)
        def keys(self):
            if self._lane is None:
                self._initalize_lanes()
            return self._lanes.keys()
        def values(self):
            if self._lane is None:
                self._initalize_lanes()
            return self._lanes.values()
        def items(self):
            if self._lane is None:
                self._initalize_lanes()
            return self._lanes.items()
        def __len__(self):
            if self._lane is None:
                self._initalize_lanes()
            return len(self._lanes)

    def __init__(self, xml=None):
        self.pathname = None
        self.tree = None

        # parse lane parameters out of the config.xml file
        self.lanes = Gerald.LaneSpecificRunParameters(self)

        self.summary = None
        self.eland_results = None

        if xml is not None:
            self.set_elements(xml)

    def _get_date(self):
        if self.tree is None:
            return datetime.today()
        timestamp = self.tree.findtext('ChipWideRunParameters/TIME_STAMP')
        if timestamp is not None:
            epochstamp = time.mktime(time.strptime(timestamp, '%c'))
            return datetime.fromtimestamp(epochstamp)
        if self.pathname is not None:
            epochstamp = os.stat(self.pathname)[stat.ST_MTIME]
            return datetime.fromtimestamp(epochstamp)
        return datetime.today()
    date = property(_get_date)

    def _get_time(self):
        return time.mktime(self.date.timetuple())
    time = property(_get_time, doc='return run time as seconds since epoch')

    def _get_experiment_root(self):
        if self.tree is None:
            return None
        return self.tree.findtext('ChipWideRunParameters/EXPT_DIR_ROOT')

    def _get_runfolder_name(self):
        if self.tree is None:
            return None

        expt_root = os.path.normpath(self._get_experiment_root())
        chip_expt_dir = self.tree.findtext('ChipWideRunParameters/EXPT_DIR')
        # hiseqs renamed the experiment dir location
        defaults_expt_dir = self.tree.findtext('Defaults/EXPT_DIR')

        experiment_dir = None
        if defaults_expt_dir is not None:
            _, experiment_dir = os.path.split(defaults_expt_dir)
        elif expt_root is not None and chip_expt_dir is not None:
            experiment_dir = chip_expt_dir.replace(expt_root+os.path.sep, '')
            experiment_dir = experiment_dir.split(os.path.sep)[0]

        if experiment_dir is None or len(experiment_dir) == 0:
            return None
        return experiment_dir

    runfolder_name = property(_get_runfolder_name)

    def _get_version(self):
        if self.tree is None:
            return None
        ga_version = self.tree.findtext(
            'ChipWideRunParameters/SOFTWARE_VERSION')
        if ga_version is not None:
            return ga_version
        hiseq_software_node = self.tree.find('Software')
        hiseq_version = hiseq_software_node.attrib['Version']
        return hiseq_version

    version = property(_get_version)

    def _get_chip_attribute(self, value):
        return self.tree.findtext('ChipWideRunParameters/%s' % (value,))

    def dump(self):
        """
        Debugging function, report current object
        """
        print 'Gerald version:', self.version
        print 'Gerald run date:', self.date
        print 'Gerald config.xml:', self.tree
        self.summary.dump()

    def get_elements(self):
        if self.tree is None or self.summary is None:
            return None

        gerald = ElementTree.Element(Gerald.GERALD,
                                     {'version': unicode(Gerald.XML_VERSION)})
        gerald.append(self.tree)
        gerald.append(self.summary.get_elements())
        if self.eland_results:
            gerald.append(self.eland_results.get_elements())
        return gerald

    def set_elements(self, tree):
        if tree.tag !=  Gerald.GERALD:
            raise ValueError('exptected GERALD')
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > Gerald.XML_VERSION:
            LOGGER.warn('XML tree is a higher version than this class')
        self.eland_results = ELAND()
        for element in list(tree):
            tag = element.tag.lower()
            if tag == Gerald.RUN_PARAMETERS.lower():
                self.tree = element
            elif tag == Gerald.SUMMARY.lower():
                self.summary = Summary(xml=element)
            elif tag == ELAND.ELAND.lower():
                self.eland_results = ELAND(xml=element)
            else:
                LOGGER.warn("Unrecognized tag %s" % (element.tag,))

def gerald(pathname):
    g = Gerald()
    g.pathname = os.path.expanduser(pathname)
    path, name = os.path.split(g.pathname)
    LOGGER.info("Parsing gerald config.xml")
    config_pathname = os.path.join(g.pathname, 'config.xml')
    g.tree = ElementTree.parse(config_pathname).getroot()

    # parse Summary.htm file
    summary_xml = os.path.join(g.pathname, 'Summary.xml')
    summary_htm = os.path.join(g.pathname, 'Summary.htm')
    status_files_summary = os.path.join(g.pathname, '..', 'Data', 'Status_Files', 'Summary.htm')
    if os.path.exists(summary_xml):
        LOGGER.info("Parsing Summary.xml")
        summary_pathname = summary_xml
    elif os.path.exists(summary_htm):
        summary_pathname = os.path.join(g.pathname, 'Summary.htm')
        LOGGER.info("Parsing Summary.htm")
    else:
        summary_pathname = status_files_summary
        LOGGER.info("Parsing %s" % (status_files_summary,))
    g.summary = Summary(summary_pathname)
    # parse eland files
    g.eland_results = eland(g.pathname, g)
    return g

if __name__ == "__main__":
  # quick test code
  import sys
  g = gerald(sys.argv[1])
  #ElementTree.dump(g.get_elements())
