"""
Analyze ELAND files
"""

from glob import glob
import logging
import os
import re
import stat

from htsworkflow.pipelines.runfolder import ElementTree
from htsworkflow.util.ethelp import indent, flatten
from htsworkflow.util.opener import autoopen

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

    ELAND_SINGLE = 0
    ELAND_MULTI = 1
    ELAND_EXTENDED = 2
    ELAND_EXPORT = 3

    def __init__(self, pathname=None, genome_map=None, eland_type=None, xml=None):
        self.pathname = pathname
        self._sample_name = None
        self._lane_id = None
        self._reads = None
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
            self.eland_type = ElandLane.ELAND_SINGLE
          elif re.search('multi', name):
            self.eland_type = ElandLane.ELAND_MULTI
          elif re.search('extended', name):
            self.eland_type = ElandLane.ELAND_EXTENDED
          elif re.search('export', name):
            self.eland_type = ElandLane.ELAND_EXPORT
          else:
            self.eland_type = ElandLane.ELAND_SINGLE

    def _update(self):
        """
        Actually read the file and actually count the reads
        """
        # can't do anything if we don't have a file to process
        if self.pathname is None:
            return
        self._guess_eland_type(self.pathname)

        if os.stat(self.pathname)[stat.ST_SIZE] == 0:
            raise RuntimeError("Eland isn't done, try again later.")

        logging.info("summarizing results for %s" % (self.pathname))

        if self.eland_type == ElandLane.ELAND_SINGLE:
          result = self._update_eland_result(self.pathname)
        elif self.eland_type == ElandLane.ELAND_MULTI or \
             self.eland_type == ElandLane.ELAND_EXTENDED:
          result = self._update_eland_multi(self.pathname)
        else:
          raise NotImplementedError("Only support single/multi/extended eland files")
        self._match_codes, self._mapped_reads, self._reads = result

    def _update_eland_result(self, pathname):
        reads = 0
        mapped_reads = {}

        match_codes = {'NM':0, 'QC':0, 'RM':0,
                       'U0':0, 'U1':0, 'U2':0,
                       'R0':0, 'R1':0, 'R2':0,
                      }
        for line in autoopen(pathname,'r'):
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

    def _update_eland_multi(self, pathname):
        reads = 0
        mapped_reads = {}

        match_codes = {'NM':0, 'QC':0, 'RM':0,
                       'U0':0, 'U1':0, 'U2':0,
                       'R0':0, 'R1':0, 'R2':0,
                      }
        match_counts_re = re.compile("([\d]+):([\d]+):([\d]+)")
        for line in autoopen(pathname,'r'):
            reads += 1
            fields = line.split()
            # fields[2] = QC/NM/or number of matches
            groups = match_counts_re.match(fields[2])
            if groups is None:
                match_codes[fields[2]] += 1
            else:
                # when there are too many hit, eland writes a - where
                # it would have put the list of hits
                if fields[3] == '-':
                  continue
                zero_mismatches = int(groups.group(1))
                if zero_mismatches == 1:
                  match_codes['U0'] += 1
                elif zero_mismatches < 255:
                  match_codes['R0'] += zero_mismatches

                one_mismatches = int(groups.group(2))
                if one_mismatches == 1:
                  match_codes['U1'] += 1
                elif one_mismatches < 255:
                  match_codes['R1'] += one_mismatches

                two_mismatches = int(groups.group(3))
                if two_mismatches == 1:
                  match_codes['U2'] += 1
                elif two_mismatches < 255:
                  match_codes['R2'] += two_mismatches

                chromo = None
                for match in fields[3].split(','):
                  match_fragment = match.split(':')
                  if len(match_fragment) == 2:
                      chromo = match_fragment[0]
                      pos = match_fragment[1]

                  fasta = self.genome_map.get(chromo, chromo)
                  assert fasta is not None
                  mapped_reads[fasta] = mapped_reads.setdefault(fasta, 0) + 1
        return match_codes, mapped_reads, reads

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

def check_for_eland_file(basedir, lane_id, pattern):
   basename = pattern % (lane_id,)
   pathname = os.path.join(basedir, basename)
   if os.path.exists(pathname):
       return pathname
   else:
       return None

def eland(basedir, gerald=None, genome_maps=None):
    e = ELAND()

    file_list = glob(os.path.join(basedir, "*_eland_result.txt"))
    if len(file_list) == 0:
        # lets handle compressed eland files too
        file_list = glob(os.path.join(basedir, "*_eland_result.txt.bz2"))

    lane_ids = ['1','2','3','4','5','6','7','8']
    # the order in patterns determines the preference for what
    # will be found.
    patterns = ['s_%s_eland_result.txt',
                's_%s_eland_result.txt.bz2',
                's_%s_eland_result.txt.gz',
                's_%s_eland_extended.txt',
                's_%s_eland_extended.txt.bz2',
                's_%s_eland_extended.txt.gz',
                's_%s_eland_multi.txt',
                's_%s_eland_multi.txt.bz2',
                's_%s_eland_multi.txt.gz',]

    for lane_id in lane_ids:
        for p in patterns:
            pathname = check_for_eland_file(basedir, lane_id, p)
            if pathname is not None:
              break
        else:
            continue
        # yes the lane_id is also being computed in ElandLane._update
        # I didn't want to clutter up my constructor
        # but I needed to persist the sample_name/lane_id for
        # runfolder summary_report
        path, name = os.path.split(pathname)
        logging.info("Adding eland file %s" %(name,))
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

def build_genome_fasta_map(genome_dir):
    # build fasta to fasta file map
    logging.info("Building genome map")
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
