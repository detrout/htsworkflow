#!/usr/bin/env python
"""
Runfolder.py can generate a xml file capturing all the 'interesting' parameters from a finished pipeline run. (using the -a option). The information currently being captured includes:

  * Flowcell ID
  * run dates
  * start/stop cycle numbers
  * Firecrest, bustard, gerald version numbers
  * Eland analysis types, and everything in the eland configuration file.
  * cluster numbers and other values from the Summary.htm 
    LaneSpecificParameters table. 
  * How many reads mapped to a genome from an eland file

The ELAND "mapped reads" counter will also check for eland squashed file
that were symlinked from another directory. This is so I can track how 
many reads landed on the genome of interest and on the spike ins. 

Basically my subdirectories something like:

genomes/hg18
genomes/hg18/chr*.2bpb <- files for hg18 genome
genomes/hg18/chr*.vld  
genomes/hg18/VATG.fa.2bp <- symlink to genomes/spikeins
genomes/spikein 

runfolder.py can also spit out a simple summary report (-s option) 
that contains the per lane post filter cluster numbers and the mapped 
read counts. (The report isn't currently very pretty)
"""
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

from gaworkflow.util.alphanum import alphanum
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
    if value.strip() == 'unknown':
	return 0, 0

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
                fasta = self._fasta_map.get(fields[6], fields[6])
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

class PipelineRun(object):
    """
    Capture "interesting" information about a pipeline run
    """
    def __init__(self, pathname, firecrest, bustard, gerald):
        self.pathname = pathname
        self._name = None
        self._flowcell_id = None
        self.firecrest = firecrest
        self.bustard = bustard
        self.gerald = gerald
    
    def _get_flowcell_id(self):
        # extract flowcell ID
        if self._flowcell_id is None:
          config_dir = os.path.join(self.pathname, 'Config')
          flowcell_id_path = os.path.join(config_dir, 'FlowcellId.xml')
          flowcell_id_tree = ElementTree.parse(flowcell_id_path)
          self._flowcell_id = flowcell_id_tree.findtext('Text')
        return self._flowcell_id
    flowcell_id = property(_get_flowcell_id)

    def _get_xml(self):
        """
        make one master xml file from all of our sub-components.
        """
        root = ElementTree.Element('PipelineRun')
        flowcell = ElementTree.SubElement(root, 'FlowcellID')
        flowcell.text = self.flowcell_id
        root.append(self.firecrest.elements)
        root.append(self.bustard.elements)
        root.append(self.gerald.elements)
        return root

    def _get_pretty_xml(self):
        """
        Generate indented xml file
        """
        root = self._get_xml()
        indent(root)
        return root
    xml = property(_get_pretty_xml)

    def _get_run_name(self):
        """
        Given a run tuple, find the latest date and use that as our name
        """
        if self._name is None:
          tmax = max(self.firecrest.time, self.bustard.time, self.gerald.time)
          timestamp = time.strftime('%Y-%m-%d', time.localtime(tmax))
          self._name = 'run_'+self.flowcell_id+"_"+timestamp+'.xml'
        return self._name
    name = property(_get_run_name)

    def save(self):
        logging.info("Saving run report "+ self.name)
        ElementTree.ElementTree(self.xml).write(self.name)

def get_runs(runfolder):
    """
    Search through a run folder for all the various sub component runs
    and then return a PipelineRun for each different combination.

    For example if there are two different GERALD runs, this will
    generate two different PipelineRun objects, that differ
    in there gerald component.
    """
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
                try:
                    g = GERALD(gerald_pathname)
                    runs.append(PipelineRun(runfolder, f, b, g))
                except IOError, e:
                    print "Ignoring", str(e)
    return runs
                
    
def extract_run_parameters(runs):
    """
    Search through runfolder_path for various runs and grab their parameters
    """
    for run in runs:
      run.save()

def summarize_mapped_reads(mapped_reads):
    """
    Summarize per chromosome reads into a genome count
    But handle spike-in/contamination symlinks seperately.
    """
    summarized_reads = {}
    genome_reads = 0
    genome = 'unknown'
    for k, v in mapped_reads.items():
        path, k = os.path.split(k)
        if len(path) > 0:
            genome = path
            genome_reads += v
        else:
            summarized_reads[k] = summarized_reads.setdefault(k, 0) + v
    summarized_reads[genome] = genome_reads
    return summarized_reads

def summary_report(runs):
    """
    Summarize cluster numbers and mapped read counts for a runfolder
    """
    for run in runs:
        # print a run name?
        print 'Summary for', run.name
        for lane in run.gerald.summary.lane_results:
            print 'lane', lane.lane, 'clusters', lane.cluster[0], '+/-',
            print lane.cluster[1]
        print ""
	# sort the report
	sample_keys = run.gerald.eland_results.results.keys()
	sample_keys.sort(alphanum)
	for sample in sample_keys:
            print '---'
	    result = run.gerald.eland_results.results[sample]
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
            summary_report(runs)
        if opt.archive:
            extract_run_parameters(runs)

    return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
