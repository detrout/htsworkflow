"""Provide access to information stored in the GERALD directory.
"""
import collections
from datetime import datetime, date
import logging
import os
import re
import stat
import time

from htsworkflow.pipelines.summary import Summary, SummaryGA, SummaryHiSeq
from htsworkflow.pipelines.eland import eland, ELAND

from htsworkflow.pipelines.runfolder import \
   ElementTree, \
   EUROPEAN_STRPTIME, \
   LANES_PER_FLOWCELL, \
   VERSION_RE
from htsworkflow.util.ethelp import indent, flatten

LOGGER = logging.getLogger(__name__)

class Alignment(object):
    """
    Capture meaning out of the GERALD directory
    """
    XML_VERSION = 1
    RUN_PARAMETERS='RunParameters'
    SUMMARY='Summary'

    def __init__(self, xml=None, pathname=None, tree=None):
        self.pathname = pathname
        self.tree = tree

        # parse lane parameters out of the config.xml file
        self.lanes = LaneSpecificRunParameters(self)

        self.summary = None
        self.eland_results = None

        if xml is not None:
            self.set_elements(xml)

    def _get_date(self):
        if self.pathname is not None:
            epochstamp = os.stat(self.pathname)[stat.ST_MTIME]
            return datetime.fromtimestamp(epochstamp)
        return datetime.today()

    def _get_time(self):
        return time.mktime(self.date.timetuple())
    time = property(_get_time, doc='return run time as seconds since epoch')

    def _get_chip_attribute(self, value):
        return self.tree.findtext('ChipWideRunParameters/%s' % (value,))

    def dump(self):
        """
        Debugging function, report current object
        """
        print 'Software:'. self.__class__.__name__
        print 'Alignment version:', self.version
        print 'Run date:', self.date
        print 'config.xml:', self.tree
        self.summary.dump()

    def get_elements(self, root_tag):
        if self.tree is None or self.summary is None:
            return None

        gerald = ElementTree.Element(root_tag,
                                     {'version': unicode(Gerald.XML_VERSION)})
        gerald.append(self.tree)
        gerald.append(self.summary.get_elements())
        if self.eland_results:
            gerald.append(self.eland_results.get_elements())
        return gerald

    def set_elements(self, tree, root_tag):
        if tree.tag !=  root_tag:
            raise ValueError('expected %s' % (self.__class__.GERALD,))
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

class Gerald(Alignment):
    GERALD='Gerald'

    def _get_date(self):
        if self.tree is None:
            return datetime.today()

        timestamp = self.tree.findtext('ChipWideRunParameters/TIME_STAMP')
        if timestamp is not None:
            epochstamp = time.mktime(time.strptime(timestamp, '%c'))
            return datetime.fromtimestamp(epochstamp)
        return super(Gerald, self)._get_date()
    date = property(_get_date)

    def get_elements(self):
        return super(Gerald, self).get_elements(Gerald.GERALD)

    def set_elements(self, tree):
        return super(Gerald, self).set_elements(tree, Gerald.GERALD)

    def _get_experiment_root(self):
        if self.tree is None:
            return None
        return self.tree.findtext('ChipWideRunParameters/EXPT_DIR_ROOT')

    def _get_runfolder_name(self):
        if self.tree is None:
            return None

        expt_root = os.path.normpath(self._get_experiment_root())
        chip_expt_dir = self.tree.findtext('ChipWideRunParameters/EXPT_DIR')

        if expt_root is not None and chip_expt_dir is not None:
            experiment_dir = chip_expt_dir.replace(expt_root+os.path.sep, '')
            experiment_dir = experiment_dir.split(os.path.sep)[0]

        if experiment_dir is None or len(experiment_dir) == 0:
            return None
        return experiment_dir

    runfolder_name = property(_get_runfolder_name)

    def _get_software_version(self):
        if self.tree is None:
            return None
        ga_version = self.tree.findtext(
            'ChipWideRunParameters/SOFTWARE_VERSION')
        if ga_version is not None:
            gerald = re.match("@.*GERALD.pl,v (?P<version>\d+(\.\d+)+)",
                             ga_version)
            if gerald:
                return ('GERALD', gerald.group('version'))
            casava = re.match('CASAVA-(?P<version>\d+[.\d]*)',
                              ga_version)
            if casava:
                return ('CASAVA', casava.group('version'))

    def _get_software(self):
        """Return name of analysis software package"""
        software_version = self._get_software_version()
        return software_version[0] if software_version is not None else None
    software = property(_get_software)

    def _get_version(self):
        """Return version number of software package"""
        software_version = self._get_software_version()
        return software_version[1] if software_version is not None else None
    version = property(_get_version)

class CASAVA(Alignment):
    GERALD='Casava'

    def __init__(self, xml=None, pathname=None, tree=None):
        super(CASAVA, self).__init__(xml=xml, pathname=pathname, tree=tree)

        self._add_timestamp()

    def _add_timestamp(self):
        """Manually add a time stamp to CASAVA runs"""
        if self.tree is None:
            return
        if len(self.tree.xpath('TIME_STAMP')) == 0:
            time_stamp = self.date.strftime('%c')
            time_element = ElementTree.Element('TIME_STAMP')
            time_element.text = time_stamp
            self.tree.append(time_element)

    def _get_date(self):
        if self.tree is None:
            return None
        time_element = self.tree.xpath('TIME_STAMP')
        if len(time_element) == 1:
            return datetime.strptime(time_element[0].text, '%c')
        return super(CASAVA, self)._get_date()
    date = property(_get_date)

    def get_elements(self):
        tree = super(CASAVA, self).get_elements(CASAVA.GERALD)
        return tree

    def set_elements(self, tree):
        return super(CASAVA, self).set_elements(tree, CASAVA.GERALD)

    def _get_runfolder_name(self):
        if self.tree is None:
            return None

        # hiseqs renamed the experiment dir location
        defaults_expt_dir = self.tree.findtext('Defaults/EXPT_DIR')
        _, experiment_dir = os.path.split(defaults_expt_dir)

        if experiment_dir is None or len(experiment_dir) == 0:
            return None
        return experiment_dir

    runfolder_name = property(_get_runfolder_name)

    def _get_software_version(self):
        if self.tree is None:
            return None
        if self.tree is None:
            return None
        hiseq_software_node = self.tree.find('Software')
        software_version = hiseq_software_node.attrib.get('Version',None)
        if software_version is None:
            return None
        return software_version.split('-')

    def _get_software(self):
        software_version = self._get_software_version()
        if software_version is None:
            return None
        return software_version[0]
    software = property(_get_software)

    def _get_version(self):
        software_version = self._get_software_version()
        if software_version is None:
            return None
        return software_version[1]
    version = property(_get_version)


class LaneParameters(object):
    """
    Make it easy to access elements of LaneSpecificRunParameters from python
    """
    def __init__(self, gerald, lane_id):
        self._gerald = gerald
        self._lane_id = lane_id

    def _get_analysis(self):
        raise NotImplemented("abstract class")
    analysis = property(_get_analysis)

    def _get_eland_genome(self):
        raise NotImplemented("abstract class")
    eland_genome = property(_get_eland_genome)

    def _get_read_length(self):
        raise NotImplemented("abstract class")
    read_length = property(_get_read_length)

    def _get_use_bases(self):
        raise NotImplemented("abstract class")
    use_bases = property(_get_use_bases)


class LaneParametersGA(LaneParameters):
    """
    Make it easy to access elements of LaneSpecificRunParameters from python
    """
    def __init__(self, gerald, lane_id):
        super(LaneParametersGA, self).__init__(gerald, lane_id)

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


class LaneParametersHiSeq(LaneParameters):
    """
    Make it easy to access elements of LaneSpecificRunParameters from python
    """
    def __init__(self, gerald, lane_id, element):
        super(LaneParametersHiSeq, self).__init__(gerald, lane_id)
        self.element = element

    def __get_attribute(self, xml_tag):
        container = self.element.find(xml_tag)
        if container is None:
            return None
        return container.text

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
        return self.__get_attribute('READ_LENGTH1')
    read_length = property(_get_read_length)

    def _get_use_bases(self):
        return self.__get_attribute('USE_BASES1')
    use_bases = property(_get_use_bases)

class LaneSpecificRunParameters(collections.MutableMapping):
    """
    Provide access to LaneSpecificRunParameters
    """
    def __init__(self, gerald):
        self._gerald = gerald
        self._lanes = None

    def _initialize_lanes(self):
        """
        build dictionary of LaneParameters
        """
        self._lanes = {}
        tree = self._gerald.tree
        analysis = tree.find('LaneSpecificRunParameters/ANALYSIS')
        if analysis is not None:
            self._extract_ga_analysis_type(analysis)
        analysis = tree.find('Projects')
        if analysis is not None:
            self._extract_hiseq_analysis_type(analysis)

    def _extract_ga_analysis_type(self, analysis):
        # according to the pipeline specs I think their fields
        # are sampleName_laneID, with sampleName defaulting to s
        # since laneIDs are constant lets just try using
        # those consistently.
        for element in analysis:
            sample, lane_id = element.tag.split('_')
            self._lanes[int(lane_id)] = LaneParametersGA(
                                          self._gerald, lane_id)

    def _extract_hiseq_analysis_type(self, analysis):
        """Extract from HiSeq style multiplexed analysis types"""
        for element in analysis:
            name = element.attrib['name']
            self._lanes[name] = LaneParametersHiSeq(self._gerald,
                                                    name,
                                                    element)

    def __iter__(self):
        if self._lanes is None:
            self._initialize_lanes()
        return self._lanes.iterkeys()

    def __getitem__(self, key):
        if self._lanes is None:
            self._initialize_lanes()
        return self._lanes[key]

    def __setitem__(self, key, value):
        self._lanes[key] = value

    def __delitem__(self, key):
        del self._lanes[key]

    def __len__(self):
        if self._lanes is None:
            self._initialize_lanes()
        return len(self._lanes)


def gerald(pathname):
    LOGGER.info("Parsing gerald config.xml")
    pathname = os.path.expanduser(pathname)
    config_pathname = os.path.join(pathname, 'config.xml')
    config_tree = ElementTree.parse(config_pathname).getroot()

    # parse Summary.htm file
    summary_xml = os.path.join(pathname, 'Summary.xml')
    summary_htm = os.path.join(pathname, 'Summary.htm')
    report_summary = os.path.join(pathname, '..', 'Data',
                                  'reports', 'Summary', )
    if os.path.exists(summary_xml):
        g = Gerald(pathname = pathname, tree=config_tree)
        LOGGER.info("Parsing Summary.xml")
        g.summary = SummaryGA(summary_xml)
        g.eland_results = eland(g.pathname, g)
    elif os.path.exists(summary_htm):
        g = Gerald(pathname=pathname, tree=config_tree)
        LOGGER.info("Parsing Summary.htm")
        g.summary = SummaryGA(summary_htm)
        g.eland_results = eland(g.pathname, g)
    elif os.path.isdir(report_summary):
        g = CASAVA(pathname=pathname, tree=config_tree)
        LOGGER.info("Parsing %s" % (report_summary,))
        g.summary = SummaryHiSeq(report_summary)
        g.eland_results = eland(g.pathname, g)

    # parse eland files
    return g

if __name__ == "__main__":
  # quick test code
  import sys
  g = gerald(sys.argv[1])
  #ElementTree.dump(g.get_elements())
