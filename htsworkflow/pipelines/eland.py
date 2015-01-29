"""
Analyze ELAND files
"""
from __future__ import print_function

import collections
from glob import glob
import logging
import os
import re
import stat
import sys
import types

from htsworkflow.pipelines import ElementTree, LANE_LIST
from htsworkflow.pipelines.samplekey import SampleKey
from htsworkflow.pipelines.genomemap import GenomeMap
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

    def __init__(self, pathnames=None, sample=None, lane_id=None, end=None,
                 xml=None):
        self.pathnames = pathnames
        self.sample_name = sample
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

    def _get_reads(self):
        if self._reads is None:
            self._update()
        return self._reads
    reads = property(_get_reads)

    def get_elements(self):
        return None

    def __repr__(self):
        name = []

        name.append('L%s' % (self.lane_id,))
        name.append('R%s' % (self.end,))
        name.append('S%s' % (self.sample_name,))

        return '<ResultLane(' + ",".join(name) + ')>'

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

    def __init__(self, pathnames=None, sample=None, lane_id=None, end=None,
                 genome_map=None, eland_type=None, xml=None):
        super(ElandLane, self).__init__(pathnames, sample, lane_id, end)

        self._mapped_reads = None
        self._match_codes = None
        self._reads = None
        self.genome_map = GenomeMap(genome_map)
        self.eland_type = None

        if xml is not None:
            self.set_elements(xml)

    def __repr__(self):
        name = []

        name.append('L%s' % (self.lane_id,))
        name.append('R%s' % (self.end,))
        name.append('S%s' % (self.sample_name,))

        reads = str(self._reads) if self._reads is not None else 'Uncounted'
        return '<ElandLane(' + ",".join(name) + ' = '+ reads + ')>'

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
                self.sample_name = element.text
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

    def __init__(self, pathnames=None, sample=None, lane_id=None, end=None,
                 xml=None):
        self.sequence_type = None
        super(SequenceLane, self).__init__(pathnames, sample, lane_id, end, xml)

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
                self.sample_name = element.text
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

class ELAND(collections.MutableMapping):
    """
    Summarize information from eland files
    """
    XML_VERSION = 3

    ELAND = 'ElandCollection'
    LANE = 'Lane'
    LANE_ID = 'id'
    SAMPLE = 'sample'
    END = 'end'

    def __init__(self, xml=None):
        # we need information from the gerald config.xml
        self.results = {}

        if xml is not None:
            self.set_elements(xml)

    def __getitem__(self, key):
        if not isinstance(key, SampleKey):
            raise ValueError("Key must be a %s" % (str(type(SampleKey))))
        return self.results[key]

    def __setitem__(self, key, value):
        if not isinstance(key, SampleKey):
            raise ValueError("Key must be a %s" % (str(type(SampleKey))))
        self.results[key] = value

    def __delitem__(self, key):
        del self.result[key]

    def __iter__(self):
        keys = self.results.iterkeys()
        for k in sorted(keys):
            yield k

    def __len__(self):
        return len(self.results)

    def find_keys(self, search):
        """Return results that match key"""
        if not isinstance(search, SampleKey):
            raise ValueError("Key must be a %s" % (str(type(SampleKey))))
        if not search.iswild:
            yield self[search]
        for key in self.keys():
            if key.matches(search): yield key

    def get_elements(self):
        root = ElementTree.Element(ELAND.ELAND,
                                   {'version': unicode(ELAND.XML_VERSION)})

        for key in self:
            eland_lane = self[key].get_elements()
            eland_lane.attrib[ELAND.END] = unicode(self[key].end-1)
            eland_lane.attrib[ELAND.LANE_ID] = unicode(self[key].lane_id)
            eland_lane.attrib[ELAND.SAMPLE] = unicode(self[key].sample_name)
            root.append(eland_lane)
        return root
        return root

    def set_elements(self, tree):
        if tree.tag.lower() != ELAND.ELAND.lower():
            raise ValueError('Expecting %s', ELAND.ELAND)
        for element in list(tree):
            lane_id = int(element.attrib[ELAND.LANE_ID])
            end = int(element.attrib.get(ELAND.END, 0))
            sample = element.attrib.get(ELAND.SAMPLE, 's')
            if element.tag.lower() == ElandLane.LANE.lower():
                lane = ElandLane(xml=element)
            elif element.tag.lower() == SequenceLane.LANE.lower():
                lane = SequenceLane(xml=element)

            key = SampleKey(lane=lane_id, read=end+1, sample=sample)
            self.results[key] = lane


    def update_result_with_eland(self, gerald, key, pathnames,
                                 genome_maps):
        # yes the lane_id is also being computed in ElandLane._update
        # I didn't want to clutter up my constructor
        # but I needed to persist the sample_name/lane_id for
        # runfolder summary_report
        names = [ os.path.split(p)[1] for p in pathnames]
        LOGGER.info("Adding eland files %s" %(",".join(names),))
        basedir = os.path.split(pathnames[0])[0]
        gs_template = "{0}_*_L{1:03}_genomesize.xml"
        genomesize = glob(
            os.path.join(basedir,
                         gs_template.format(key.sample, key.lane)))


        genome_map = GenomeMap()
        if genome_maps is not None:
            genome_map = GenomeMap(genome_maps[key.lane])
        elif len(genomesize) > 0:
            LOGGER.info("Found {0}".format(genomesize))
            genome_map.parse_genomesize(genomesize[0])
        elif gerald is not None:
            genome_dir = gerald.lanes[key].eland_genome
            if genome_dir is not None:
                genome_map.scan_genome_dir(genome_dir)

        lane = ElandLane(pathnames, key.sample, key.lane, key.read, genome_map)

        self.results[key] = lane

    def update_result_with_sequence(self, gerald, key, pathnames,
                                    genome_maps=None):
        self.results[key] = SequenceLane(pathnames,
                                         key.sample, key.lane, key.read)


def eland(gerald_dir, gerald=None, genome_maps=None):
    e = ELAND()
    eland_files = ElandMatches(e)
    # collect
    for path, dirnames, filenames in os.walk(gerald_dir):
        for filename in filenames:
            pathname = os.path.abspath(os.path.join(path, filename))
            eland_files.add(pathname)
    for key in eland_files:
        eland_files.count(key, gerald, genome_maps)
    return e


class ElandMatches(collections.MutableMapping):
    def __init__(self, eland_container):
        # the order in patterns determines the preference for what
        # will be found.
        self.eland_container = eland_container
        MAPPED = eland_container.update_result_with_eland
        SEQUENCE = eland_container.update_result_with_sequence

        sample = '(?P<sample>[^_]+)'
        hiIndex = '_(?P<index>(NoIndex|[AGCT])+)'
        hiLane = '_L(?P<lane>[\d]+)'
        gaLane = '_(?P<lane>[\d]+)'
        hiRead = '_R(?P<read>[\d]+)'
        gaRead = '(_(?P<read>[\d])+)?'
        part = '_(?P<part>[\d]+)'
        ext = '(?P<extention>(\.bz2|\.gz)?)'

        hiPrefix = sample + hiIndex + hiLane + hiRead + part
        gaPrefix = sample + gaLane + gaRead
        P = collections.namedtuple('Patterns', 'pattern counter priority')
        self.patterns = [
            P(hiPrefix +'_export.txt' + ext, MAPPED, 6),
            P(gaPrefix + '_eland_result.txt' + ext, MAPPED, 5),
            P(gaPrefix + '_eland_extended.txt' + ext, MAPPED, 4),
            P(gaPrefix + '_eland_multi.txt' + ext, MAPPED, 3),
            P(gaPrefix + '_export.txt' + ext, MAPPED, 2),
            P(gaPrefix + '_sequence.txt' + ext, SEQUENCE, 1),
            ]
        self.file_sets = {}
        self.file_priority = {}
        self.file_counter = {}

    def add(self, pathname):
        """Add pathname to our set of files
        """
        path, filename = os.path.split(pathname)

        for pattern, counter, priority in self.patterns:
            rematch = re.match(pattern, filename)
            if rematch is not None:
                m = ElandMatch(pathname, counter, **rematch.groupdict())
                key = m.make_samplekey()
                old_priority = self.file_priority.get(key, 0)
                if priority > old_priority:
                    self.file_sets[key] = set((m,))
                    self.file_counter[key] = counter
                    self.file_priority[key] = priority
                elif priority == old_priority:
                    self.file_sets[key].add(m)

    def count(self, key, gerald=None, genome_maps=None):
        #previous sig: gerald, e.results, lane_id, end, pathnames, genome_maps
        counter = self.file_counter[key]
        file_set = self.file_sets[key]
        filenames = [ f.filename for f in file_set ]
        return counter(gerald, key,
                       filenames, genome_maps)

    def __iter__(self):
        return iter(self.file_sets)

    def __len__(self):
        return len(self.file_sets)

    def __getitem__(self, key):
        return self.file_sets[key]

    def __setitem__(self, key, value):
        if not isintance(value, set):
            raise ValueError("Expected set for value")
        self.file_sets[key] = value

    def __delitem__(self, key):
        del self.file_sets[key]

class ElandMatch(object):
    def __init__(self, pathname, counter,
                 lane=None, read=None, extension=None,
                 sample=None, index=None, part=None, **kwargs):
        self.filename = pathname
        self.counter = counter
        self._lane = lane
        self._read = read
        self.extension = extension
        self.sample = sample
        self.index = index
        self._part = part
        LOGGER.info("Found %s: L%s R%s Samp%s" % (
            self.filename, self._lane, self._read, self.sample))

    def make_samplekey(self):
        read = self._read if self._read is not None else 1
        return SampleKey(lane=self.lane, read=read, sample=self.sample)

    def _get_lane(self):
        if self._lane is not None:
            return int(self._lane)
        return self._lane
    lane = property(_get_lane)

    def _get_read(self):
        if self._read is not None:
            return int(self._read)
        return self._read
    read = property(_get_read)

    def _get_part(self):
        if self._part is not None:
            return int(self._part)
        return self._part
    part = property(_get_part)

    def __repr__(self):
        name = []
        if self.sample is not None: name.append(self.sample)
        if self._lane is not None: name.append('L%s' % (self.lane,))
        if self._read is not None: name.append('R%s' % (self.read,))
        if self._part is not None: name.append('P%s' % (self.part,))
        return '<ElandMatch(' + "_".join(name) + ')>'


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
        print(ElementTree.tostring(e.get_elements()))
    return


if __name__ == "__main__":
    main(sys.argv[1:])
