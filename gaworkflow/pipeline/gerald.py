"""
Provide access to information stored in the GERALD directory.
"""
from datetime import datetime, date
from glob import glob
import logging
import os
import stat
import time

from gaworkflow.pipeline.runfolder import \
   ElementTree, \
   EUROPEAN_STRPTIME, \
   LANES_PER_FLOWCELL, \
   VERSION_RE
from gaworkflow.util.ethelp import indent, flatten
from gaworkflow.util.opener import autoopen

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
        def __init__(self, gerald, key):
            self._gerald = gerald
            self._key = key
        
        def __get_attribute(self, xml_tag):
            subtree = self._gerald.tree.find('LaneSpecificRunParameters')
            container = subtree.find(xml_tag)
            if container is None:
                return None
            if len(container.getchildren()) != LANES_PER_FLOWCELL:
                raise RuntimeError('GERALD config.xml file changed')
            lanes = [x.tag.split('_')[1] for x in container.getchildren()]
            index = lanes.index(self._key)
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
            self._keys = None
        def __getitem__(self, key):
            return Gerald.LaneParameters(self._gerald, key)
        def keys(self):
            if self._keys is None:
                tree = self._gerald.tree
                analysis = tree.find('LaneSpecificRunParameters/ANALYSIS')
                # according to the pipeline specs I think their fields 
                # are sampleName_laneID, with sampleName defaulting to s
                # since laneIDs are constant lets just try using 
                # those consistently.
                self._keys = [ x.tag.split('_')[1] for x in analysis]
            return self._keys
        def values(self):
            return [ self[x] for x in self.keys() ]
        def items(self):
            return zip(self.keys(), self.values())
        def __len__(self):
            return len(self.keys())

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
    config_pathname = os.path.join(pathname, 'config.xml')
    g.tree = ElementTree.parse(config_pathname).getroot()

    # parse Summary.htm file
    summary_pathname = os.path.join(pathname, 'Summary.htm')
    g.summary = Summary(summary_pathname)
    # parse eland files
    g.eland_results = eland(g.pathname, g)
    return g

def tonumber(v):
    """
    Convert a value to int if its an int otherwise a float.
    """
    try:
        v = int(v)
    except ValueError, e:
        v = float(v)
    return v

def parse_mean_range(value):
    """
    Parse values like 123 +/- 4.5
    """
    if value.strip() == 'unknown':
	return 0, 0

    average, pm, deviation = value.split()
    if pm != '+/-':
        raise RuntimeError("Summary.htm file format changed")
    return tonumber(average), tonumber(deviation)

def make_mean_range_element(parent, name, mean, deviation):
    """
    Make an ElementTree subelement <Name mean='mean', deviation='deviation'/>
    """
    element = ElementTree.SubElement(parent, name,
                                     { 'mean': unicode(mean),
                                       'deviation': unicode(deviation)})
    return element

def parse_mean_range_element(element):
    """
    Grab mean/deviation out of element
    """
    return (tonumber(element.attrib['mean']), 
            tonumber(element.attrib['deviation']))

class Summary(object):
    """
    Extract some useful information from the Summary.htm file
    """
    XML_VERSION = 1
    SUMMARY = 'Summary'

    class LaneResultSummary(object):
        """
        Parse the LaneResultSummary table out of Summary.htm
        Mostly for the cluster number
        """
        LANE_RESULT_SUMMARY = 'LaneResultSummary'
        TAGS = { 
          'Cluster': 'cluster',
          'AverageFirstCycleIntensity': 'average_first_cycle_intensity',
          'PercentIntensityAfter20Cycles': 'percent_intensity_after_20_cycles',
          'PercentPassFilterClusters': 'percent_pass_filter_clusters',
          'PercentPassFilterAlign': 'percent_pass_filter_align',
          'AverageAlignmentScore': 'average_alignment_score',
          'PercentErrorRate': 'percent_error_rate'
        }
                 
        def __init__(self, html=None, xml=None):
            self.lane = None
            self.cluster = None
            self.average_first_cycle_intensity = None
            self.percent_intensity_after_20_cycles = None
            self.percent_pass_filter_clusters = None
            self.percent_pass_filter_align = None
            self.average_alignment_score = None
            self.percent_error_rate = None

            if html is not None:
                self.set_elements_from_html(html)
            if xml is not None:
                self.set_elements(xml)

        def set_elements_from_html(self, data):
            if not len(data) in (8,10):
                raise RuntimeError("Summary.htm file format changed")

            # same in pre-0.3.0 Summary file and 0.3 summary file
            self.lane = data[0]

            if len(data) == 8:
                # this is the < 0.3 Pipeline version
                self.cluster = parse_mean_range(data[1])
                self.average_first_cycle_intensity = parse_mean_range(data[2])
                self.percent_intensity_after_20_cycles = \
                    parse_mean_range(data[3])
                self.percent_pass_filter_clusters = parse_mean_range(data[4])
                self.percent_pass_filter_align = parse_mean_range(data[5])
                self.average_alignment_score = parse_mean_range(data[6])
                self.percent_error_rate = parse_mean_range(data[7])
            elif len(data) == 10:
                # this is the >= 0.3 summary file
                self.cluster_raw = data[1]
                self.cluster = parse_mean_range(data[2])
                # FIXME: think of generic way to capture the variable data
                

        def get_elements(self):
            lane_result = ElementTree.Element(
                            Summary.LaneResultSummary.LANE_RESULT_SUMMARY, 
                            {'lane': self.lane})
            for tag, variable_name in Summary.LaneResultSummary.TAGS.items():
                element = make_mean_range_element(
                    lane_result,
                    tag,
                    *getattr(self, variable_name)
                )
            return lane_result

        def set_elements(self, tree):
            if tree.tag != Summary.LaneResultSummary.LANE_RESULT_SUMMARY:
                raise ValueError('Expected %s' % (
                        Summary.LaneResultSummary.LANE_RESULT_SUMMARY))
            self.lane = tree.attrib['lane']
            tags = Summary.LaneResultSummary.TAGS
            for element in list(tree):
                try:
                    variable_name = tags[element.tag]
                    setattr(self, variable_name, 
                            parse_mean_range_element(element))
                except KeyError, e:
                    logging.warn('Unrecognized tag %s' % (element.tag,))

    def __init__(self, filename=None, xml=None):
        self.lane_results = {}

        if filename is not None:
            self._extract_lane_results(filename)
        if xml is not None:
            self.set_elements(xml)

    def __getitem__(self, key):
        return self.lane_results[key]

    def __len__(self):
        return len(self.lane_results)

    def keys(self):
        return self.lane_results.keys()

    def values(self):
        return self.lane_results.values()

    def items(self):
        return self.lane_results.items()

    def _flattened_row(self, row):
        """
        flatten the children of a <tr>...</tr>
        """
        return [flatten(x) for x in row.getchildren() ]
    
    def _parse_table(self, table):
        """
        assumes the first line is the header of a table, 
        and that the remaining rows are data
        """
        rows = table.getchildren()
        data = []
        for r in rows:
            data.append(self._flattened_row(r))
        return data
    
    def _extract_named_tables(self, pathname):
        """
        extract all the 'named' tables from a Summary.htm file
        and return as a dictionary
        
        Named tables are <h2>...</h2><table>...</table> pairs
        The contents of the h2 tag is considered to the name
        of the table.
        """
        tree = ElementTree.parse(pathname).getroot()
        body = tree.find('body')
        tables = {}
        for i in range(len(body)):
            if body[i].tag == 'h2' and body[i+1].tag == 'table':
                # we have an interesting table
                name = flatten(body[i])
                table = body[i+1]
                data = self._parse_table(table)
                tables[name] = data
        return tables

    def _extract_lane_results(self, pathname):
        """
        extract the Lane Results Summary table
        """

        tables = self._extract_named_tables(pathname)

        # parse lane result summary
        lane_summary = tables['Lane Results Summary']
        # this is version 1 of the summary file
        if len(lane_summary[-1]) == 8:
            # strip header
            headers = lane_summary[0]
            # grab the lane by lane data
            lane_summary = lane_summary[1:]

        # this is version 2 of the summary file
        if len(lane_summary[-1]) == 10:
            # lane_summary[0] is a different less specific header row
            headers = lane_summary[1]
            lane_summary = lane_summary[2:10]
            # after the last lane, there's a set of chip wide averages

        for r in lane_summary:
            lrs = Summary.LaneResultSummary(html=r)
            self.lane_results[lrs.lane] = lrs

    def get_elements(self):
        summary = ElementTree.Element(Summary.SUMMARY, 
                                      {'version': unicode(Summary.XML_VERSION)})
        for lane in self.lane_results.values():
            summary.append(lane.get_elements())
        return summary

    def set_elements(self, tree):
        if tree.tag != Summary.SUMMARY:
            return ValueError("Expected %s" % (Summary.SUMMARY,))
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > Summary.XML_VERSION:
            logging.warn('Summary XML tree is a higher version than this class')
        for element in list(tree):
            lrs = Summary.LaneResultSummary()
            lrs.set_elements(element)
            self.lane_results[lrs.lane] = lrs

    def dump(self):
        """
        Debugging function, report current object
        """
        pass


def build_genome_fasta_map(genome_dir):
    # build fasta to fasta file map
    genome = genome_dir.split(os.path.sep)[-1]
    fasta_map = {}
    for vld_file in glob(os.path.join(genome_dir, '*.vld')):
        is_link = False
        if os.path.islink(vld_file):
            is_link = True
        vld_file = os.path.realpath(vld_file)
        path, vld_name = os.path.split(vld_file)
        name, ext = os.path.splitext(vld_name)
        if is_link:
            fasta_map[name] = name
        else:
            fasta_map[name] = os.path.join(genome, name)
    return fasta_map
    
class ElandLane(object):
    """
    Process an eland result file
    """
    XML_VERSION = 1
    LANE = 'ElandLane'
    SAMPLE_NAME = 'SampleName'
    LANE_ID = 'LaneID'
    GENOME_MAP = 'GenomeMap'
    GENOME_ITEM = 'GenomeItem'
    MAPPED_READS = 'MappedReads'
    MAPPED_ITEM = 'MappedItem'
    MATCH_CODES = 'MatchCodes'
    MATCH_ITEM = 'Code'
    READS = 'Reads'

    def __init__(self, pathname=None, genome_map=None, xml=None):
        self.pathname = pathname
        self._sample_name = None
        self._lane_id = None
        self._reads = None
        self._mapped_reads = None
        self._match_codes = None
        if genome_map is None:
            genome_map = {}
        self.genome_map = genome_map
        
        if xml is not None:
            self.set_elements(xml)

    def _update(self):
        """
        Actually read the file and actually count the reads
        """
        # can't do anything if we don't have a file to process
        if self.pathname is None:
            return

        if os.stat(self.pathname)[stat.ST_SIZE] == 0:
            raise RuntimeError("Eland isn't done, try again later.")

        reads = 0
        mapped_reads = {}

        match_codes = {'NM':0, 'QC':0, 'RM':0, 
                       'U0':0, 'U1':0, 'U2':0,
                       'R0':0, 'R1':0, 'R2':0,
                      }
        for line in autoopen(self.pathname,'r'):
            reads += 1
            fields = line.split()
            # code = fields[2]
            # match_codes[code] = match_codes.setdefault(code, 0) + 1
            # the QC/NM etc codes are in the 3rd field and always present
            match_codes[fields[2]] += 1
            # ignore lines that don't have a fasta filename
            if len(fields) < 7:
                continue
            fasta = self.genome_map.get(fields[6], fields[6])
            mapped_reads[fasta] = mapped_reads.setdefault(fasta, 0) + 1
        self._match_codes = match_codes
        self._mapped_reads = mapped_reads
        self._reads = reads

    def _update_name(self):
        # extract the sample name
        if self.pathname is None:
            return

        path, name = os.path.split(self.pathname)
        split_name = name.split('_')
        self._sample_name = split_name[0]
        self._lane_id = split_name[1]

    def _get_sample_name(self):
        if self._sample_name is None:
            self._update_name()
        return self._sample_name
    sample_name = property(_get_sample_name)

    def _get_lane_id(self):
        if self._lane_id is None:
            self._update_name()
        return self._lane_id
    lane_id = property(_get_lane_id)

    def _get_reads(self):
        if self._reads is None:
            self._update()
        return self._reads
    reads = property(_get_reads)

    def _get_mapped_reads(self):
        if self._mapped_reads is None:
            self._update()
        return self._mapped_reads
    mapped_reads = property(_get_mapped_reads)

    def _get_match_codes(self):
        if self._match_codes is None:
            self._update()
        return self._match_codes
    match_codes = property(_get_match_codes)

    def get_elements(self):
        lane = ElementTree.Element(ElandLane.LANE, 
                                   {'version': 
                                    unicode(ElandLane.XML_VERSION)})
        sample_tag = ElementTree.SubElement(lane, ElandLane.SAMPLE_NAME)
        sample_tag.text = self.sample_name
        lane_tag = ElementTree.SubElement(lane, ElandLane.LANE_ID)
        lane_tag.text = self.lane_id
        genome_map = ElementTree.SubElement(lane, ElandLane.GENOME_MAP)
        for k, v in self.genome_map.items():
            item = ElementTree.SubElement(
                genome_map, ElandLane.GENOME_ITEM, 
                {'name':k, 'value':unicode(v)})
        mapped_reads = ElementTree.SubElement(lane, ElandLane.MAPPED_READS)
        for k, v in self.mapped_reads.items():
            item = ElementTree.SubElement(
                mapped_reads, ElandLane.MAPPED_ITEM, 
                {'name':k, 'value':unicode(v)})
        match_codes = ElementTree.SubElement(lane, ElandLane.MATCH_CODES)
        for k, v in self.match_codes.items():
            item = ElementTree.SubElement(
                match_codes, ElandLane.MATCH_ITEM, 
                {'name':k, 'value':unicode(v)})
        reads = ElementTree.SubElement(lane, ElandLane.READS)
        reads.text = unicode(self.reads)

        return lane

    def set_elements(self, tree):
        if tree.tag != ElandLane.LANE:
            raise ValueError('Exptecting %s' % (ElandLane.LANE,))

        # reset dictionaries
        self._mapped_reads = {}
        self._match_codes = {}
        
        for element in tree:
            tag = element.tag.lower()
            if tag == ElandLane.SAMPLE_NAME.lower():
                self._sample_name = element.text
            elif tag == ElandLane.LANE_ID.lower():
                self._lane_id = element.text
            elif tag == ElandLane.GENOME_MAP.lower():
                for child in element:
                    name = child.attrib['name']
                    value = child.attrib['value']
                    self.genome_map[name] = value
            elif tag == ElandLane.MAPPED_READS.lower():
                for child in element:
                    name = child.attrib['name']
                    value = child.attrib['value']
                    self._mapped_reads[name] = int(value)
            elif tag == ElandLane.MATCH_CODES.lower():
                for child in element:
                    name = child.attrib['name']
                    value = int(child.attrib['value'])
                    self._match_codes[name] = value
            elif tag == ElandLane.READS.lower():
                self._reads = int(element.text)
            else:
                logging.warn("ElandLane unrecognized tag %s" % (element.tag,))

def extract_eland_sequence(instream, outstream, start, end):
    """
    Extract a chunk of sequence out of an eland file
    """
    for line in instream:
        record = line.split()
        if len(record) > 1:
            result = [record[0], record[1][start:end]]
        else:
            result = [record[0][start:end]]
        outstream.write("\t".join(result))
        outstream.write(os.linesep)

class ELAND(object):
    """
    Summarize information from eland files
    """
    XML_VERSION = 1

    ELAND = 'ElandCollection'
    LANE = 'Lane'
    LANE_ID = 'id'

    def __init__(self, xml=None):
        # we need information from the gerald config.xml
        self.results = {}
        
        if xml is not None:
            self.set_elements(xml)

    def __len__(self):
        return len(self.results)

    def keys(self):
        return self.results.keys()
    
    def values(self):
        return self.results.values()

    def items(self):
        return self.results.items()

    def __getitem__(self, key):
        return self.results[key]

    def get_elements(self):
        root = ElementTree.Element(ELAND.ELAND, 
                                   {'version': unicode(ELAND.XML_VERSION)})
        for lane_id, lane in self.results.items():
            eland_lane = lane.get_elements()
            eland_lane.attrib[ELAND.LANE_ID] = unicode(lane_id)
            root.append(eland_lane)
        return root

    def set_elements(self, tree):
        if tree.tag.lower() != ELAND.ELAND.lower():
            raise ValueError('Expecting %s', ELAND.ELAND)
        for element in list(tree):
            lane_id = element.attrib[ELAND.LANE_ID]
            lane = ElandLane(xml=element)
            self.results[lane_id] = lane

def eland(basedir, gerald=None, genome_maps=None):
    e = ELAND()

    file_list = glob(os.path.join(basedir, "*_eland_result.txt"))
    if len(file_list) == 0:
        # lets handle compressed eland files too
        file_list = glob(os.path.join(basedir, "*_eland_result.txt.bz2"))

    for pathname in file_list:
        # yes the lane_id is also being computed in ElandLane._update
        # I didn't want to clutter up my constructor
        # but I needed to persist the sample_name/lane_id for
        # runfolder summary_report
        path, name = os.path.split(pathname)
        split_name = name.split('_')
        lane_id = split_name[1]

        if genome_maps is not None:
            genome_map = genome_maps[lane_id]
        elif gerald is not None:
            genome_dir = gerald.lanes[lane_id].eland_genome
            genome_map = build_genome_fasta_map(genome_dir)
        else:
            genome_map = {}

        eland_result = ElandLane(pathname, genome_map)
        e.results[lane_id] = eland_result
    return e
