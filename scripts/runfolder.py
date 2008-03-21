#!/usr/bin/env python
import time
import logging
import os
import re
import stat
import sys
from glob import glob
from pprint import pprint
import optparse

try:
  from xml.etree import ElementTree
except ImportError, e:
  from elementtree import ElementTree

EUROPEAN_STRPTIME = "%d-%m-%Y"
EUROPEAN_DATE_RE = "([0-9]{1,2}-[0-9]{1,2}-[0-9]{4,4})"
VERSION_RE = "([0-9\.]+)"
USER_RE = "([a-zA-Z0-9]+)"
LANES_PER_FLOWCELL = 8

runfolder_path = '/home/diane/gec/080221_HWI-EAS229_0018_201BHAAXX'

def indent(elem, level=0):
    """
    reformat an element tree to be 'pretty' (indented)
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level+1)
        # we don't want the closing tag indented too far
        child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def flatten(elem, include_tail=0):
    """
    Extract the text from an element tree 
    (AKA extract the text that not part of XML tags)
    """
    text = elem.text or ""
    for e in elem:
        text += flatten(e, 1)
    if include_tail and elem.tail: text += elem.tail
    return text

class Firecrest(object):
    def __init__(self, pathname):
        self.pathname = pathname

        # parse firecrest directory name
        path, name = os.path.split(pathname)
        groups = name.split('_')
        # grab the start/stop cycle information
        cycle = re.match("C([0-9]+)-([0-9]+)", groups[0])
        self.start = int(cycle.group(1))
        self.stop = int(cycle.group(2))
        # firecrest version
        version = re.search(VERSION_RE, groups[1])
        self.version = (version.group(1))
        # datetime
        self.date = time.strptime(groups[2], EUROPEAN_STRPTIME)
        self.time = time.mktime(self.date)
        # username
        self.user = groups[3]

        # should I parse this deeper than just stashing the 
        # contents of the matrix file?
        matrix_pathname = os.path.join(self.pathname, 'Matrix', 's_matrix.txt')
        self.matrix = open(matrix_pathname, 'r').read()
        
    def dump(self):
        print "Starting cycle:", self.start
        print "Ending cycle:", self.stop
        print "Firecrest version:", self.version
        print "Run date:", self.date
        print "user:", self.user

    def _get_elements(self):
        firecrest = ElementTree.Element('Firecrest')
        version = ElementTree.SubElement(firecrest, 'version')
        version.text = self.version
        start_cycle = ElementTree.SubElement(firecrest, 'FirstCycle')
        start_cycle.text = str(self.start)
        stop_cycle = ElementTree.SubElement(firecrest, 'LastCycle')
        stop_cycle.text = str(self.stop)
        run_date = ElementTree.SubElement(firecrest, 'run_time')
        run_date.text = str(self.time)
        matrix = ElementTree.SubElement(firecrest, 'matrix')
        matrix.text = self.matrix
        return firecrest
    elements=property(_get_elements)

class Bustard(object):
    def __init__(self, pathname):
        self.pathname = pathname

        path, name = os.path.split(pathname)
        groups = name.split("_")
        version = re.search(VERSION_RE, groups[0])
        self.version = version.group(1)
        self.date = time.strptime(groups[1], EUROPEAN_STRPTIME)
        self.time = time.mktime(self.date)
        self.user = groups[2]
        self.phasing = {}
        self._load_params()

    def _load_params(self):
        paramfiles = glob(os.path.join(self.pathname, "params*"))
        for paramfile in paramfiles:
            path, name = os.path.split(paramfile)
            basename, ext = os.path.splitext(name)
            # the last character of the param filename should be the
            # lane number
            lane = int(basename[-1])
            # we want the whole tree, not just the stuff under
            # the first tag
            param_tree = ElementTree.parse(paramfile).getroot()
            self.phasing[lane] = param_tree

    def dump(self):
        print "Bustard version:", self.version
        print "Run date", self.date
        print "user:", self.user
        for lane, tree in self.phasing.items():
            print lane
            print tree

    def _get_elements(self):
        bustard = ElementTree.Element('Bustard')
        version = ElementTree.SubElement(bustard, 'version')
        version.text = self.version
        run_date = ElementTree.SubElement(bustard, 'run_time')
        run_date.text = str(self.time)
        return bustard
    elements=property(_get_elements)
        
class GERALD(object):
    """
    Capture meaning out of the GERALD directory
    """
    class LaneParameters(object):
        """
        Make it easy to access elements of LaneSpecificRunParameters from python
        """
        def __init__(self, tree, key):
            self._tree = tree.find('LaneSpecificRunParameters')
            self._key = key
        
        def __get_attribute(self, xml_tag):
            container = self._tree.find(xml_tag)
            if container is None or \
               len(container.getchildren()) != LANES_PER_FLOWCELL:
                raise RuntimeError('GERALD config.xml file changed')
            element = container.find(self._key)
            return element.text
        def _get_analysis(self):
            return self.__get_attribute('ANALYSIS')
        analysis = property(_get_analysis)

        def _get_eland_genome(self):
            return self.__get_attribute('ELAND_GENOME')
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
        def __init__(self, tree):
            self._tree = tree
            self._keys = None
        def __getitem__(self, key):
            return GERALD.LaneParameters(self._tree, key)
        def keys(self):
            if self._keys is None:
                analysis = self._tree.find('LaneSpecificRunParameters/ANALYSIS')
                self._keys = [ x.tag for x in analysis]
            return self._keys
        def values(self):
            return [ self[x] for x in self.keys() ]
        def items(self):
            return zip(self.keys(), self.values())
        def __len__(self):
            return len(self.keys)

    def __init__(self, pathname):
        self.pathname = pathname
        path, name = os.path.split(pathname)
        config_pathname = os.path.join(self.pathname, 'config.xml')
        self.tree = ElementTree.parse(config_pathname).getroot()
        self.version = self.tree.findtext('ChipWideRunParameters/SOFTWARE_VERSION')

        date = self.tree.findtext('ChipWideRunParameters/TIME_STAMP')
        self.date = time.strptime(date)
        self.time = time.mktime(self.date)
        
        # parse Summary.htm file
        summary_pathname = os.path.join(self.pathname, 'Summary.htm')
        self.summary = Summary(summary_pathname)
        self.lanes = GERALD.LaneSpecificRunParameters(self.tree)
        self.eland_results = ELAND(self, self.pathname)

    def dump(self):
        """
        Debugging function, report current object
        """
        print 'Gerald version:', self.version
        print 'Gerald run date:', self.date
        print 'Gerald config.xml:', self.tree
        self.summary.dump()

    def _get_elements(self):
        gerald = ElementTree.Element('Gerald')
        gerald.append(self.tree)
        gerald.append(self.summary.elements)
        return gerald
    elements = property(_get_elements)

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
    average, pm, deviation = value.split()
    if pm != '+/-':
        raise RuntimeError("Summary.htm file format changed")
    return tonumber(average), tonumber(deviation)

def mean_range_element(parent, name, mean, deviation):
    """
    Make an ElementTree subelement <Name mean='mean', deviation='deviation'/>
    """
    element = ElementTree.SubElement(parent, name,
                                     { 'mean': str(mean),
                                       'deviation': str(deviation)})
    return element

class LaneResultSummary(object):
    """
    Parse the LaneResultSummary table out of Summary.htm
    Mostly for the cluster number
    """
    def __init__(self, row_element):
        data = [ flatten(x) for x in row_element ]
        if len(data) != 8:
            raise RuntimeError("Summary.htm file format changed")

        self.lane = data[0]
        self.cluster = parse_mean_range(data[1])
        self.average_first_cycle_intensity = parse_mean_range(data[2])
        self.percent_intensity_after_20_cycles = parse_mean_range(data[3])
        self.percent_pass_filter_clusters = parse_mean_range(data[4])
        self.percent_pass_filter_align = parse_mean_range(data[5])
        self.average_alignment_score = parse_mean_range(data[6])
        self.percent_error_rate = parse_mean_range(data[7])

    def _get_elements(self):
        lane_result = ElementTree.Element('LaneResultSummary', 
                                          {'lane': self.lane})
        cluster = mean_range_element(lane_result, 'Cluster', *self.cluster)
        first_cycle = mean_range_element(lane_result, 
                                         'AverageFirstCycleIntensity',
                                         *self.average_first_cycle_intensity)
        after_20 = mean_range_element(lane_result,
                                      'PercentIntensityAfter20Cycles',
                                      *self.percent_intensity_after_20_cycles)
        pass_filter = mean_range_element(lane_result,
                                         'PercentPassFilterClusters',
                                         *self.percent_pass_filter_clusters)
        alignment = mean_range_element(lane_result,
                                       'AverageAlignmentScore',
                                       *self.average_alignment_score)
        error_rate = mean_range_element(lane_result,
                                        'PercentErrorRate',
                                        *self.percent_error_rate)
        return lane_result
    elements = property(_get_elements)

class Summary(object):
    """
    Extract some useful information from the Summary.htm file
    """
    def __init__(self, pathname):
        self.pathname = pathname
        self.tree = ElementTree.parse(pathname).getroot()
        self.lane_results = []

        self._extract_lane_results()

    def _extract_lane_results(self):
        """
        extract the Lane Results Summary table
        """
        if flatten(self.tree.findall('*//h2')[3]) != 'Lane Results Summary':
            raise RuntimeError("Summary.htm file format changed")

        table = self.tree.findall('*//table')[2]
        rows = table.getchildren()
        headers = rows[0].getchildren()
        if flatten(headers[2]) != 'Av 1st Cycle Int ':
            raise RuntimeError("Summary.htm file format changed")

        for r in rows[1:]:
            self.lane_results.append(LaneResultSummary(r))

    def _get_elements(self):
        summary = ElementTree.Element('Summary')
        for lane in self.lane_results:
            summary.append(lane.elements)
        return summary
    elements = property(_get_elements)

    def dump(self):
        """
        Debugging function, report current object
        """
        pass

    
class ELAND(object):
    """
    Summarize information from eland files
    """
    class ElandResult(object):
        """
        Process an eland result file
        """
        def __init__(self, gerald, pathname):
            self.gerald = gerald
            self.pathname = pathname
            # extract the sample name
            path, name = os.path.split(self.pathname)
            self.sample_name = name.replace("_eland_result.txt","")
            self._reads = None
            self._mapped_reads = None
            self._fasta_map = {}

        def _build_fasta_map(self, genome_dir):
            # build fasta to fasta file map
            fasta_map = {}
            for vld_file in glob(os.path.join(genome_dir, '*.vld')):
                if os.path.islink(vld_file):
                    vld_file = os.path.realpath(vld_file)
                path, vld_name = os.path.split(vld_file)
                name, ext = os.path.splitext(vld_name)
                fasta_map[name] = (path, name)
            # strip the common path prefix
            paths = [ x[0] for x in fasta_map.values() ]
            common_path = os.path.commonprefix(paths)
            # FIXME:
            # don't do this
            # In [161]: gerald.eland_results.results['s_1'].mapped_reads
            # Out[161]: {'5.fa': 98417, '3.fa': 90226, '4.fa': 66373, '1.fa': 105589, '2.fa': 77904}

            for k, (path, name) in fasta_map.items():
                fasta_map[k] = os.path.join(path.replace(common_path, ''), name)
            self._fasta_map = fasta_map

        def _update(self):
            """
            Actually read the file and actually count the reads
            """
            if os.stat(self.pathname)[stat.ST_SIZE] == 0:
                raise RuntimeError("Eland isn't done, try again later.")
            
            reads = 0
            mapped_reads = {}
            genome_dir = self.gerald.lanes[self.sample_name].eland_genome
            self._build_fasta_map(genome_dir)

            for line in open(self.pathname):
                reads += 1
                fields = line.split()
                # ignore lines that don't have a fasta filename
                if len(fields) < 7:
                    continue
                fasta = self._fasta_map[fields[6]]
                mapped_reads[fasta] = mapped_reads.setdefault(fasta, 0) + 1
            self._mapped_reads = mapped_reads
            self._reads = reads
        
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
            
    def __init__(self, gerald, basedir):
        # we need information from the gerald config.xml
        self.gerald = gerald
        self.results = {}
        for f in glob(os.path.join(basedir, "*_eland_result.txt")):
            eland_result = ELAND.ElandResult(gerald, f)
            self.results[eland_result.sample_name] = eland_result

def get_runs(runfolder):
    datadir = os.path.join(runfolder, 'Data')

    logging.info('Searching for runs in ' + datadir)
    runs = []
    for firecrest_pathname in glob(os.path.join(datadir,"*Firecrest*")):
        f = Firecrest(firecrest_pathname)
        bustard_glob = os.path.join(firecrest_pathname, "Bustard*")
        for bustard_pathname in glob(bustard_glob):
            b = Bustard(bustard_pathname)
            gerald_glob = os.path.join(bustard_pathname, 'GERALD*')
            for gerald_pathname in glob(gerald_glob):
                g = GERALD(gerald_pathname)
                runs.append((f, b, g))
    return runs
                
def format_run(run):
    """
    Given a run tuple making a single formatted xml file
    """
    firecrest, bustard, gerald = run
    root = ElementTree.Element('Run')
    root.append(firecrest.elements)
    root.append(bustard.elements)
    root.append(gerald.elements)
    indent(root)
    return root
       
def make_run_name(run):
    """
    Given a run tuple, find the latest date and use that as our name
    """
    firecrest, bustard, gerald = run
    tmax = max(firecrest.time, bustard.time, gerald.time)
    timestamp = time.strftime('%Y-%m-%d', time.localtime(tmax))
    name = 'run-'+timestamp+'.xml'
    return name
    
def extract_run_parameters(runs):
    """
    Search through runfolder_path for various runs and grab their parameters
    """
    for run in runs:
        tree = format_run(run)
        name = make_run_name(run)
        logging.info("Saving run report "+ name)
        ElementTree.ElementTree(tree).write(name)

def summary(runs):
    def summarize_mapped_reads(mapped_reads):
        summarized_reads = {}
        genome_reads = 0
        for k, v in mapped_reads.items():
            if 'chr' in k:
                genome_reads += v
                genome = os.path.split(k)[0]
            else:
                summarized_reads[k] = summarized_reads.setdefault(k, 0) + v
        summarized_reads[genome] = genome_reads
        return summarized_reads

    for run in runs:
        # print a run name?
        logging.info('Summarizing ' + str(run))
        gerald = run[2]
        for lane in gerald.summary.lane_results:
            print 'lane', lane.lane, 'clusters', lane.cluster[0], '+/-',
            print lane.cluster[1]
        print ""
        for sample, result in gerald.eland_results.results.items():
            print '---'
            print "Sample name", sample
            print "Total Reads", result.reads
            print "Mapped Reads"
            pprint(summarize_mapped_reads(result.mapped_reads))

def make_parser():
    usage = 'usage: %prog [options] runfolder_root_dir'
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                      default=False,
                      help='turn on verbose mode')
    parser.add_option('-s', '--summary', dest='summary', action='store_true',
                      default=False,
                      help='produce summary report')
    parser.add_option('-a', '--archive', dest='archive', action='store_true',
                      default=False,
                      help='generate run configuration archive')
    return parser

def main(cmdlist=None):
    parser = make_parser()
    opt, args = parser.parse_args(cmdlist)

    if len(args) == 0:
        parser.error('need path to a runfolder')
    
    logging.basicConfig()
    if opt.verbose:
        root_log = logging.getLogger()
        root_log.setLevel(logging.INFO)

    for runfolder in args:
        runs = get_runs(runfolder)
        if opt.summary:
            summary(runs)
        if opt.archive:
            extract_run_parameters(runs)

    return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
