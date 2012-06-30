"""
Analyze ELAND files
"""
import collections
from glob import glob
import logging
import os
import re
import stat
import sys

from htsworkflow.pipelines.runfolder import ElementTree, LANE_LIST
from htsworkflow.util.ethelp import indent, flatten
from htsworkflow.util.opener import autoopen

LOGGER = logging.getLogger(__name__)

SAMPLE_NAME = 'SampleName'
LANE_ID = 'LaneID'
END = 'End'
READS = 'Reads'

GENOME_MAP = 'GenomeMap'
GENOME_ITEM = 'GenomeItem'
MAPPED_READS = 'MappedReads'
MAPPED_ITEM = 'MappedItem'
MATCH_CODES = 'MatchCodes'
MATCH_ITEM = 'Code'
READS = 'Reads'

ELAND_SINGLE = 0
ELAND_MULTI = 1
ELAND_EXTENDED = 2
ELAND_EXPORT = 3

class ResultLane(object):
    """
    Base class for result lanes
    """
    XML_VERSION = 2
    LANE = 'ResultLane'

    def __init__(self, pathnames=None, lane_id=None, end=None, xml=None):
        self.pathnames = pathnames
        self._sample_name = None
        self.lane_id = lane_id
        self.end = end
        self._reads = None

        if xml is not None:
            self.set_elements(xml)

    def _update(self):
        """
        Actually read the file and actually count the reads
        """
        pass

    def _update_name(self):
        # extract the sample name
        if self.pathnames is None or len(self.pathnames) == 0:
            return

        sample_names = set()
        for pathname in self.pathnames:
            path, name = os.path.split(pathname)
            split_name = name.split('_')
            sample_names.add(split_name[0])
        if len(sample_names) > 1:
            errmsg = "Attempting to update from more than one sample %s"
            raise RuntimeError(errmsg % (",".join(sample_names)))
        self._sample_name = sample_names.pop()
        return self._sample_name

    def _get_sample_name(self):
        if self._sample_name is None:
            self._update_name()
        return self._sample_name
    sample_name = property(_get_sample_name)

    def _get_reads(self):
        if self._reads is None:
            self._update()
        return self._reads
    reads = property(_get_reads)

    def get_elements(self):
        return None

class ElandLane(ResultLane):
    """
    Process an eland result file
    """
    XML_VERSION = 2
    LANE = "ElandLane"
    MATCH_COUNTS_RE = re.compile("([\d]+):([\d]+):([\d]+)")
    DESCRIPTOR_MISMATCH_RE = re.compile("[AGCT]")
    DESCRIPTOR_INDEL_RE = re.compile("^[\dAGCT]$")
    SCORE_UNRECOGNIZED = 0
    SCORE_QC = 1
    SCORE_READ = 2

    def __init__(self, pathnames=None, lane_id=None, end=None, genome_map=None, eland_type=None, xml=None):
        super(ElandLane, self).__init__(pathnames, lane_id, end)

        self._mapped_reads = None
        self._match_codes = None
        if genome_map is None:
            genome_map = {}
        self.genome_map = genome_map
        self.eland_type = None

        if xml is not None:
            self.set_elements(xml)

    def _guess_eland_type(self, pathname):
        if self.eland_type is None:
          # attempt autodetect eland file type
          pathn, name = os.path.split(pathname)
          if re.search('result', name):
            self.eland_type = ELAND_SINGLE
          elif re.search('multi', name):
            self.eland_type = ELAND_MULTI
          elif re.search('extended', name):
            self.eland_type = ELAND_EXTENDED
          elif re.search('export', name):
            self.eland_type = ELAND_EXPORT
          else:
            self.eland_type = ELAND_SINGLE

    def _update(self):
        """
        Actually read the file and actually count the reads
        """
        # can't do anything if we don't have a file to process
        if self.pathnames is None or len(self.pathnames) == 0:
            return
        pathname = self.pathnames[-1]
        self._guess_eland_type(pathname)

        if os.stat(pathname)[stat.ST_SIZE] == 0:
            raise RuntimeError("Eland isn't done, try again later.")

        LOGGER.debug("summarizing results for %s" % (pathname))
        self._match_codes = MatchCodes()
        self._mapped_reads = MappedReads()
        self._reads = 0

        for pathname in self.pathnames:
            stream = autoopen(pathname, 'r')
            if self.eland_type == ELAND_SINGLE:
                result = self._update_eland_result(stream)
            elif self.eland_type == ELAND_MULTI or \
                 self.eland_type == ELAND_EXTENDED:
                result = self._update_eland_multi(stream)
            elif self.eland_type == ELAND_EXPORT:
                result = self._update_eland_export(stream)
            else:
                errmsg = "Only support single/multi/extended eland files"
                raise NotImplementedError(errmsg)
            stream.close()

            match, mapped, reads = result
            self._match_codes += match
            self._mapped_reads += mapped
            self._reads += reads

    def _update_eland_result(self, instream):
        reads = 0
        mapped_reads = MappedReads()
        match_codes = MatchCodes()

        for line in instream:
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
        return match_codes, mapped_reads, reads

    def _update_eland_multi(self, instream):
        """Summarize an eland_extend."""
        MATCH_INDEX = 2
        LOCATION_INDEX = 3
        reads = 0
        mapped_reads = MappedReads()
        match_codes = MatchCodes()

        for line in instream:
            reads += 1
            fields = line.split()
            # fields[2] = QC/NM/or number of matches
            score_type = self._score_mapped_mismatches(fields[MATCH_INDEX],
                                                       match_codes)
            if score_type == ElandLane.SCORE_READ:
                # when there are too many hits, eland  writes a - where
                # it would have put the list of hits.
                # or in a different version of eland, it just leaves
                # that column blank, and only outputs 3 fields.
                if len(fields) < 4 or fields[LOCATION_INDEX] == '-':
                  continue

                self._count_mapped_multireads(mapped_reads, fields[LOCATION_INDEX])

        return match_codes, mapped_reads, reads

    def _update_eland_export(self, instream):
        """Summarize a gerald export file."""
        MATCH_INDEX = 10
        LOCATION_INDEX = 10
        DESCRIPTOR_INDEX= 13
        reads = 0
        mapped_reads = MappedReads()
        match_codes = MatchCodes()

        for line in instream:
            reads += 1
            fields = line.split()
            # fields[2] = QC/NM/or number of matches
            score_type = self._score_mapped_mismatches(fields[MATCH_INDEX],
                                                       match_codes)
            if score_type == ElandLane.SCORE_UNRECOGNIZED:
                # export files have three states for the match field
                # QC code, count of multi-reads, or a single
                # read location. The score_mapped_mismatches function
                # only understands the first two types.
                # if we get unrecognized, that implies the field is probably
                # a location.
                code = self._count_mapped_export(mapped_reads,
                                                 fields[LOCATION_INDEX],
                                                 fields[DESCRIPTOR_INDEX])
                match_codes[code] += 1

        return match_codes, mapped_reads, reads


    def _score_mapped_mismatches(self, match, match_codes):
        """Update match_codes with eland map counts, or failure code.

        Returns True if the read mapped, false if it was an error code.
        """
        groups = ElandLane.MATCH_COUNTS_RE.match(match)
        if groups is None:
            # match is not of the form [\d]+:[\d]+:[\d]+
            if match in match_codes:
                # match is one quality control codes QC/NM etc
                match_codes[match] += 1
                return ElandLane.SCORE_QC
            else:
                return ElandLane.SCORE_UNRECOGNIZED
        else:
            # match is of the form [\d]+:[\d]+:[\d]+
            # AKA Multiread
            zero_mismatches = int(groups.group(1))
            one_mismatches = int(groups.group(2))
            two_mismatches = int(groups.group(3))

            if zero_mismatches == 1:
                match_codes['U0'] += 1
            elif zero_mismatches < 255:
                match_codes['R0'] += zero_mismatches

            if one_mismatches == 1:
                match_codes['U1'] += 1
            elif one_mismatches < 255:
                match_codes['R1'] += one_mismatches

            if two_mismatches == 1:
                match_codes['U2'] += 1
            elif two_mismatches < 255:
                match_codes['R2'] += two_mismatches

            return ElandLane.SCORE_READ


    def _count_mapped_multireads(self, mapped_reads, match_string):
        chromo = None
        for match in match_string.split(','):
            match_fragment = match.split(':')
            if len(match_fragment) == 2:
                chromo = match_fragment[0]
                pos = match_fragment[1]

            fasta = self.genome_map.get(chromo, chromo)
            assert fasta is not None
            mapped_reads[fasta] = mapped_reads.setdefault(fasta, 0) + 1


    def _count_mapped_export(self, mapped_reads, match_string, descriptor):
        """Count a read as defined in an export file

        match_string contains the chromosome
        descriptor contains the an ecoding of bases that match, mismatch,
                   and have indels.
        returns the "best" match code

        Currently "best" match code is ignoring the possibility of in-dels
        """
        chromo = match_string
        fasta = self.genome_map.get(chromo, chromo)
        assert fasta is not None
        mapped_reads[fasta] = mapped_reads.setdefault(fasta, 0) + 1

        mismatch_bases = ElandLane.DESCRIPTOR_MISMATCH_RE.findall(descriptor)
        if len(mismatch_bases) == 0:
            return 'U0'
        elif len(mismatch_bases) == 1:
            return 'U1'
        else:
            return 'U2'


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

    def _get_no_match(self):
        if self._mapped_reads is None:
            self._update()
        return self._match_codes['NM']
    no_match = property(_get_no_match,
                        doc="total reads that didn't match the target genome.")

    def _get_no_match_percent(self):
        return float(self.no_match)/self.reads * 100
    no_match_percent = property(_get_no_match_percent,
                                doc="no match reads as percent of total")

    def _get_qc_failed(self):
        if self._mapped_reads is None:
            self._update()
        return self._match_codes['QC']
    qc_failed = property(_get_qc_failed,
                        doc="total reads that didn't match the target genome.")

    def _get_qc_failed_percent(self):
        return float(self.qc_failed)/self.reads * 100
    qc_failed_percent = property(_get_qc_failed_percent,
                                 doc="QC failed reads as percent of total")

    def _get_unique_reads(self):
        if self._mapped_reads is None:
           self._update()
        sum = 0
        for code in ['U0','U1','U2']:
            sum += self._match_codes[code]
        return sum
    unique_reads = property(_get_unique_reads,
                            doc="total unique reads")

    def _get_repeat_reads(self):
        if self._mapped_reads is None:
           self._update()
        sum = 0
        for code in ['R0','R1','R2']:
            sum += self._match_codes[code]
        return sum
    repeat_reads = property(_get_repeat_reads,
                            doc="total repeat reads")

    def get_elements(self):
        lane = ElementTree.Element(ElandLane.LANE,
                                   {'version':
                                    unicode(ElandLane.XML_VERSION)})
        sample_tag = ElementTree.SubElement(lane, SAMPLE_NAME)
        sample_tag.text = self.sample_name
        lane_tag = ElementTree.SubElement(lane, LANE_ID)
        lane_tag.text = str(self.lane_id)
        if self.end is not None:
            end_tag = ElementTree.SubElement(lane, END)
            end_tag.text = str(self.end)
        genome_map = ElementTree.SubElement(lane, GENOME_MAP)
        for k, v in self.genome_map.items():
            item = ElementTree.SubElement(
                genome_map, GENOME_ITEM,
                {'name':k, 'value':unicode(v)})
        mapped_reads = ElementTree.SubElement(lane, MAPPED_READS)
        for k, v in self.mapped_reads.items():
            item = ElementTree.SubElement(
                mapped_reads, MAPPED_ITEM,
                {'name':k, 'value':unicode(v)})
        match_codes = ElementTree.SubElement(lane, MATCH_CODES)
        for k, v in self.match_codes.items():
            item = ElementTree.SubElement(
                match_codes, MATCH_ITEM,
                {'name':k, 'value':unicode(v)})
        reads = ElementTree.SubElement(lane, READS)
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
            if tag == SAMPLE_NAME.lower():
                self._sample_name = element.text
            elif tag == LANE_ID.lower():
                self.lane_id = int(element.text)
            elif tag == END.lower():
                self.end = int(element.text)
            elif tag == GENOME_MAP.lower():
                for child in element:
                    name = child.attrib['name']
                    value = child.attrib['value']
                    self.genome_map[name] = value
            elif tag == MAPPED_READS.lower():
                for child in element:
                    name = child.attrib['name']
                    value = child.attrib['value']
                    self._mapped_reads[name] = int(value)
            elif tag == MATCH_CODES.lower():
                for child in element:
                    name = child.attrib['name']
                    value = int(child.attrib['value'])
                    self._match_codes[name] = value
            elif tag == READS.lower():
                self._reads = int(element.text)
            else:
                LOGGER.warn("ElandLane unrecognized tag %s" % (element.tag,))


class MatchCodes(collections.MutableMapping):
    """Mapping to hold match counts -
    supports combining two match count sets together
    """
    def __init__(self, initializer=None):
        self.match_codes = {'NM':0, 'QC':0, 'RM':0,
                            'U0':0, 'U1':0, 'U2':0,
                            'R0':0, 'R1':0, 'R2':0,
                            }

        if initializer is not None:
            if not isinstance(initializer, collections.Mapping):
                raise ValueError("Expected dictionary like class")
            for key in initializer:
                if key not in self.match_codes:
                    errmsg = "Initializer can only contain: %s"
                    raise ValueError(errmsg % (",".join(self.match_codes.keys())))
                self.match_codes[key] += initializer[key]

    def __iter__(self):
        return iter(self.match_codes)

    def __delitem__(self, key):
        raise RuntimeError("delete not allowed")

    def __getitem__(self, key):
        return self.match_codes[key]

    def __setitem__(self, key, value):
        if key not in self.match_codes:
            errmsg = "Unrecognized key, allowed values are: %s"
            raise ValueError(errmsg % (",".join(self.match_codes.keys())))
        self.match_codes[key] = value

    def __len__(self):
        return len(self.match_codes)

    def __add__(self, other):
        if not isinstance(other, MatchCodes):
            raise ValueError("Expected a MatchCodes, got %s", str(type(other)))

        newobj = MatchCodes(self)
        for key, value in other.items():
            newobj[key] = self.get(key, 0) + other[key]

        return newobj


class MappedReads(collections.MutableMapping):
    """Mapping to hold mapped reads -
    supports combining two mapped read sets together
    """
    def __init__(self, initializer=None):
        self.mapped_reads = {}

        if initializer is not None:
            if not isinstance(initializer, collections.Mapping):
                raise ValueError("Expected dictionary like class")
            for key in initializer:
                self[key] = self.setdefault(key, 0) + initializer[key]

    def __iter__(self):
        return iter(self.mapped_reads)

    def __delitem__(self, key):
        del self.mapped_reads[key]

    def __getitem__(self, key):
        return self.mapped_reads[key]

    def __setitem__(self, key, value):
        self.mapped_reads[key] = value

    def __len__(self):
        return len(self.mapped_reads)

    def __add__(self, other):
        if not isinstance(other, MappedReads):
            raise ValueError("Expected a MappedReads, got %s", str(type(other)))

        newobj = MappedReads(self)
        for key in other:
            newobj[key] = self.get(key, 0) + other[key]

        return newobj

class SequenceLane(ResultLane):
    XML_VERSION=1
    LANE = 'SequenceLane'
    SEQUENCE_TYPE = 'SequenceType'

    NONE_TYPE = None
    SCARF_TYPE = 1
    FASTQ_TYPE = 2
    SEQUENCE_DESCRIPTION = { NONE_TYPE: 'None', SCARF_TYPE: 'SCARF', FASTQ_TYPE: 'FASTQ' }

    def __init__(self, pathname=None, lane_id=None, end=None, xml=None):
        self.sequence_type = None
        super(SequenceLane, self).__init__(pathname, lane_id, end, xml)

    def _guess_sequence_type(self, pathname):
        """
        Determine if we have a scarf or fastq sequence file
        """
        f = open(pathname,'r')
        l = f.readline()
        f.close()

        if l[0] == '@':
            # fastq starts with a @
            self.sequence_type = SequenceLane.FASTQ_TYPE
        else:
            self.sequence_type = SequenceLane.SCARF_TYPE
        return self.sequence_type

    def _update(self):
        """
        Actually read the file and actually count the reads
        """
        # can't do anything if we don't have a file to process
        if self.pathnames is None:
            return

        pathname = self.pathnames[-1]
        if os.stat(pathname)[stat.ST_SIZE] == 0:
            raise RuntimeError("Sequencing isn't done, try again later.")

        self._guess_sequence_type(pathname)

        LOGGER.info("summarizing results for %s" % (pathname))
        lines = 0
        f = open(pathname)
        for l in f.xreadlines():
            lines += 1
        f.close()

        if self.sequence_type == SequenceLane.SCARF_TYPE:
            self._reads = lines
        elif self.sequence_type == SequenceLane.FASTQ_TYPE:
            self._reads = lines / 4
        else:
            errmsg = "This only supports scarf or fastq squence files"
            raise NotImplementedError(errmsg)

    def get_elements(self):
        lane = ElementTree.Element(SequenceLane.LANE,
                                   {'version':
                                    unicode(SequenceLane.XML_VERSION)})
        sample_tag = ElementTree.SubElement(lane, SAMPLE_NAME)
        sample_tag.text = self.sample_name
        lane_tag = ElementTree.SubElement(lane, LANE_ID)
        lane_tag.text = str(self.lane_id)
        if self.end is not None:
            end_tag = ElementTree.SubElement(lane, END)
            end_tag.text = str(self.end)
        reads = ElementTree.SubElement(lane, READS)
        reads.text = unicode(self.reads)
        sequence_type = ElementTree.SubElement(lane, SequenceLane.SEQUENCE_TYPE)
        sequence_type.text = unicode(SequenceLane.SEQUENCE_DESCRIPTION[self.sequence_type])

        return lane

    def set_elements(self, tree):
        if tree.tag != SequenceLane.LANE:
            raise ValueError('Exptecting %s' % (SequenceLane.LANE,))
        lookup_sequence_type = dict([ (v,k) for k,v in SequenceLane.SEQUENCE_DESCRIPTION.items()])

        for element in tree:
            tag = element.tag.lower()
            if tag == SAMPLE_NAME.lower():
                self._sample_name = element.text
            elif tag == LANE_ID.lower():
                self.lane_id = int(element.text)
            elif tag == END.lower():
                self.end = int(element.text)
            elif tag == READS.lower():
                self._reads = int(element.text)
            elif tag == SequenceLane.SEQUENCE_TYPE.lower():
                self.sequence_type = lookup_sequence_type.get(element.text, None)
            else:
                LOGGER.warn("SequenceLane unrecognized tag %s" % (element.tag,))

class ELAND(object):
    """
    Summarize information from eland files
    """
    XML_VERSION = 3

    ELAND = 'ElandCollection'
    LANE = 'Lane'
    LANE_ID = 'id'
    END = 'end'

    def __init__(self, xml=None):
        # we need information from the gerald config.xml
        self.results = [{},{}]

        if xml is not None:
            self.set_elements(xml)

        if len(self.results[0]) == 0:
            # Initialize our eland object with meaningless junk
            for l in  LANE_LIST:
                self.results[0][l] = ResultLane(lane_id=l, end=0)


    def get_elements(self):
        root = ElementTree.Element(ELAND.ELAND,
                                   {'version': unicode(ELAND.XML_VERSION)})
        for end in range(len(self.results)):
           end_results = self.results[end]
           for lane_id, lane in end_results.items():
                eland_lane = lane.get_elements()
                if eland_lane is not None:
                    eland_lane.attrib[ELAND.END] = unicode (end)
                    eland_lane.attrib[ELAND.LANE_ID] = unicode(lane_id)
                    root.append(eland_lane)
        return root

    def set_elements(self, tree):
        if tree.tag.lower() != ELAND.ELAND.lower():
            raise ValueError('Expecting %s', ELAND.ELAND)
        for element in list(tree):
            lane_id = int(element.attrib[ELAND.LANE_ID])
            end = int(element.attrib.get(ELAND.END, 0))
            if element.tag.lower() == ElandLane.LANE.lower():
                lane = ElandLane(xml=element)
            elif element.tag.lower() == SequenceLane.LANE.lower():
                lane = SequenceLane(xml=element)

            self.results[end][lane_id] = lane

def check_for_eland_file(basedir, pattern, lane_id, end):
   #if end is None:
   #   full_lane_id = lane_id
   #else:
   #   full_lane_id = "%d_%d" % ( lane_id, end )
   eland_files = []
   eland_pattern = pattern % (lane_id, end)
   eland_re = re.compile(eland_pattern)
   LOGGER.debug("Eland pattern: %s" %(eland_pattern,))
   for filename in os.listdir(basedir):
       if eland_re.match(filename):
           LOGGER.info('found eland file %s' % (filename,))
           eland_files.append(os.path.join(basedir, filename))

   return eland_files

def update_result_with_eland(gerald, results, lane_id, end, pathnames, genome_maps):
    # yes the lane_id is also being computed in ElandLane._update
    # I didn't want to clutter up my constructor
    # but I needed to persist the sample_name/lane_id for
    # runfolder summary_report
    names = [ os.path.split(p)[1] for p in pathnames]
    LOGGER.info("Adding eland files %s" %(",".join(names),))

    genome_map = {}
    if genome_maps is not None:
        genome_map = genome_maps[lane_id]
    elif gerald is not None:
        genome_dir = gerald.lanes[lane_id].eland_genome
        if genome_dir is not None:
            genome_map = build_genome_fasta_map(genome_dir)

    lane = ElandLane(pathnames, lane_id, end, genome_map)

    if end is None:
        effective_end =  0
    else:
        effective_end = end - 1

    results[effective_end][lane_id] = lane

def update_result_with_sequence(gerald, results, lane_id, end, pathname):
    result = SequenceLane(pathname, lane_id, end)

    if end is None:
        effective_end =  0
    else:
        effective_end = end - 1

    results[effective_end][lane_id] = result


def eland(gerald_dir, gerald=None, genome_maps=None):
    e = ELAND()

    lane_ids = range(1,9)
    ends = [None, 1, 2]

    basedirs = [gerald_dir]

    # if there is a basedir/Temp change basedir to point to the temp
    # directory, as 1.1rc1 moves most of the files we've historically
    # cared about to that subdirectory.
    # we should look into what the official 'result' files are.
    # and 1.3 moves them back
    basedir_temp = os.path.join(gerald_dir, 'Temp')
    if os.path.isdir(basedir_temp):
        basedirs.append(basedir_temp)

    # So how about scanning for Project*/Sample* directories as well
    sample_pattern = os.path.join(gerald_dir, 'Project_*', 'Sample_*')
    basedirs.extend(glob(sample_pattern))

    # the order in patterns determines the preference for what
    # will be found.
    MAPPED_ELAND = 0
    SEQUENCE = 1
    patterns = [
        ('(?P<sampleId>[^_]+)_(?P<index>(NoIndex|[AGCT])+)_L00%s(_R%s)_(?P<part>[\d]+)_export.txt(?P<ext>(\.bz2|\.gz)?)', MAPPED_ELAND),
        ('s_(?P<lane>%s)(_(?P<end>%s))?_eland_result.txt(?P<ext>(\.bz2|\.gz)?)',
         MAPPED_ELAND),
        ('s_(?P<lane>%s)(_(?P<end>%s))?_eland_extended.txt(?P<ext>(\.bz2|\.gz)?)',
         MAPPED_ELAND),
        ('s_(?P<lane>%s)(_(?P<end>%s))?_eland_multi.txt(?P<ext>(\.bz2|\.gz)?)',
         MAPPED_ELAND),
        ('s_(?P<lane>%s)(_(?P<end>%s))?_export.txt(?P<ext>(\.bz2|\.gz)?)',
         MAPPED_ELAND),
        ('s_(?P<lane>%s)(_(?P<end>%s))?_sequence.txt(?P<ext>(\.bz2|\.gz)?)',
         SEQUENCE),

        #('s_%s_eland_result.txt', MAPPED_ELAND),
        #('s_%s_eland_result.txt.bz2', MAPPED_ELAND),
        #('s_%s_eland_result.txt.gz', MAPPED_ELAND),
        #('s_%s_eland_extended.txt', MAPPED_ELAND),
        #('s_%s_eland_extended.txt.bz2', MAPPED_ELAND),
        #('s_%s_eland_extended.txt.gz', MAPPED_ELAND),
        #('s_%s_eland_multi.txt', MAPPED_ELAND),
        #('s_%s_eland_multi.txt.bz2', MAPPED_ELAND),
        #('s_%s_eland_multi.txt.gz', MAPPED_ELAND),
        #('s_%s_export.txt', MAPPED_ELAND),
        #('s_%s_export.txt.bz2', MAPPED_ELAND),
        #('s_%s_export.txt.gz', MAPPED_ELAND),
        #('s_%s_sequence.txt', SEQUENCE),
        ]

    for basedir in basedirs:
        for end in ends:
            for lane_id in lane_ids:
                for p in patterns:
                    pathnames = check_for_eland_file(basedir, p[0], lane_id, end)
                    if len(pathnames) > 0:
                        if p[1] == MAPPED_ELAND:
                            update_result_with_eland(gerald, e.results, lane_id, end, pathnames, genome_maps)
                        elif p[1] == SEQUENCE:
                            update_result_with_sequence(gerald, e.results, lane_id, end, pathnames)
                        break
                else:
                    LOGGER.debug("No eland file found in %s for lane %s and end %s" %(basedir, lane_id, end))
                    continue

    return e

def build_genome_fasta_map(genome_dir):
    # build fasta to fasta file map
    LOGGER.info("Building genome map")
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


def main(cmdline=None):
    """Run eland extraction against the specified gerald directory"""
    from optparse import OptionParser
    parser = OptionParser("%prog: <gerald dir>+")
    opts, args = parser.parse_args(cmdline)
    logging.basicConfig(level=logging.DEBUG)
    for a in args:
        LOGGER.info("Starting scan of %s" % (a,))
        e = eland(a)
        print e.get_elements()

    return


if __name__ == "__main__":
    main(sys.argv[1:])
