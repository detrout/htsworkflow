"""
Provide access to information stored in the GERALD directory.
"""
from datetime import datetime, date
import logging
import os
import time

from htsworkflow.pipelines.summary import Summary
from htsworkflow.pipelines.eland import eland, ELAND

from htsworkflow.pipelines.runfolder import \
   ElementTree, \
   EUROPEAN_STRPTIME, \
   LANES_PER_FLOWCELL, \
   VERSION_RE
from htsworkflow.util.ethelp import indent, flatten

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
            index = lanes.index(self._lane_id)
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
                subtree = self._gerald.tree.find('ChipWideRunParameters')
                container = subtree.find('ELAND_GENOME')
                genome = container.text
            return genome
        eland_genome = property(_get_eland_genome)

        def _get_read_length(self):
            return self.__get_attribute('READ_LENGTH')
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
        epochstamp = time.mktime(time.strptime(timestamp, '%c'))
        return datetime.fromtimestamp(epochstamp)
    date = property(_get_date)

    def _get_time(self):
        return time.mktime(self.date.timetuple())
    time = property(_get_time, doc='return run time as seconds since epoch')

    def _get_version(self):
        if self.tree is None:
            return None
        return self.tree.findtext('ChipWideRunParameters/SOFTWARE_VERSION')
    version = property(_get_version)

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
            logging.warn('XML tree is a higher version than this class')
        for element in list(tree):
            tag = element.tag.lower()
            if tag == Gerald.RUN_PARAMETERS.lower():
                self.tree = element
            elif tag == Gerald.SUMMARY.lower():
                self.summary = Summary(xml=element)
            elif tag == ELAND.ELAND.lower():
                self.eland_results = ELAND(xml=element)
            else:
                logging.warn("Unrecognized tag %s" % (element.tag,))


def gerald(pathname):
    g = Gerald()
    g.pathname = pathname
    path, name = os.path.split(pathname)
    logging.info("Parsing gerald config.xml")
    config_pathname = os.path.join(pathname, 'config.xml')
    g.tree = ElementTree.parse(config_pathname).getroot()

    # parse Summary.htm file
    logging.info("Parsing Summary.htm")
    summary_pathname = os.path.join(pathname, 'Summary.htm')
    g.summary = Summary(summary_pathname)
    # parse eland files
    g.eland_results = eland(g.pathname, g)
    return g

if __name__ == "__main__":
  # quick test code
  import sys
  g = gerald(sys.argv[1])
  #ElementTree.dump(g.get_elements())
