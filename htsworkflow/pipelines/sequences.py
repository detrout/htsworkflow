"""
Utilities to work with the various eras of sequence archive files
"""
import collections
import logging
import os
import types
import re
import sys
from six.moves.urllib.parse import urljoin, urlparse

import RDF
from htsworkflow.util.rdfhelp import libraryOntology as libNS
from htsworkflow.util.rdfhelp import toTypedNode, fromTypedNode, rdfNS, \
     strip_namespace, dump_model, simplify_uri

LOGGER = logging.getLogger(__name__)

eland_re = re.compile('s_(?P<lane>\d)(_(?P<read>\d))?_eland_')
raw_seq_re = re.compile('woldlab_[0-9]{6}_[^_]+_[\d]+_[\dA-Za-z]+')
qseq_re = re.compile('woldlab_[0-9]{6}_[^_]+_[\d]+_[\dA-Za-z]+_l[\d]_r[\d].tar.bz2')

SEQUENCE_TABLE_NAME = "sequences"
def create_sequence_table(cursor):
    """
    Create a SQL table to hold  SequenceFile entries
    """
    sql = """
CREATE TABLE %(table)s (
  filetype   CHAR(8),
  path       TEXT,
  flowcell   CHAR(8),
  lane       INTEGER,
  read       INTEGER,
  pf         BOOLEAN,
  cycle      CHAR(8)
);
""" %( {'table': SEQUENCE_TABLE_NAME} )
    return cursor.execute(sql)

FlowcellPath = collections.namedtuple('FlowcellPath',
                                      'flowcell start stop project')

class SequenceFile(object):
    """
    Simple container class that holds the path to a sequence archive
    and basic descriptive information.
    """
    def __init__(self, filetype, path, flowcell, lane,
                 read=None,
                 pf=None,
                 cycle=None,
                 project=None,
                 index=None,
                 split=None):
        """Store various fields used in our sequence files

        filetype is one of 'qseq', 'srf', 'fastq'
        path = location of file
        flowcell = files flowcell id
        lane = which lane
        read = which sequencer read, usually 1 or 2
        pf = did it pass filter
        cycle = cycle dir name e.g. C1-202
        project = projed name from HiSeq, probably library ID
        index = HiSeq barcode index sequence
        split = file fragment from HiSeq (Since one file is split into many)
        """
        self.filetype = filetype
        self.path = path
        self.flowcell = flowcell
        self.lane = lane
        self.read = read
        self.pf = pf
        self.cycle = cycle
        self.project = project
        self.index = index
        self.split = split

    def __hash__(self):
        return hash(self.key())

    def key(self):
        return (self.flowcell, self.lane, self.read, self.project, self.split)

    def __str__(self):
        return str(self.path)

    def __eq__(self, other):
        """
        Equality is defined if everything but the path matches
        """
        attributes = ['filetype',
                      'flowcell',
                      'lane',
                      'read',
                      'pf',
                      'cycle',
                      'project',
                      'index',
                      'split']
        for a in attributes:
            if getattr(self, a) != getattr(other, a):
                return False

        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return u"<%s %s %s %s>" % (self.filetype, self.flowcell, self.lane, self.path)

    def make_target_name(self, root):
        """
        Create target name for where we need to link this sequence too
        """
        path, basename = os.path.split(self.path)
        # Because the names aren't unque we include the flowcel name
        # because there were different eland files for different length
        # analyses, we include the cycle length in the name.
        if self.filetype == 'eland':
            template = "%(flowcell)s_%(cycle)s_%(eland)s"
            basename = template % { 'flowcell': self.flowcell,
                                    'cycle': self.cycle,
                                    'eland': basename }
        # else:
        # all the other file types have names that include flowcell/lane
        # information and thus are unique so we don't have to do anything
        return os.path.join(root, basename)

    def save_to_sql(self, cursor):
        """
        Add this entry to a DB2.0 database.
        """
        #FIXME: NEEDS SQL ESCAPING
        header_macro = {'table': SEQUENCE_TABLE_NAME }
        sql_header = "insert into %(table)s (" % header_macro
        sql_columns = ['filetype','path','flowcell','lane']
        sql_middle = ") values ("
        sql_values = [self.filetype, self.path, self.flowcell, self.lane]
        sql_footer = ");"
        for name in ['read', 'pf', 'cycle']:
            value = getattr(self, name)
            if value is not None:
                sql_columns.append(name)
                sql_values.append(value)

        sql = " ".join([sql_header,
                        ", ".join(sql_columns),
                        sql_middle,
                        # note the following makes a string like ?,?,?
                        ",".join(["?"] * len(sql_values)),
                        sql_footer])

        return cursor.execute(sql, sql_values)

    def save_to_model(self, model, base_url=None):
        def add_lit(model, s, p, o):
            if o is not None:
                model.add_statement(RDF.Statement(s, p, toTypedNode(o)))
        def add(model, s, p, o):
            model.add_statement(RDF.Statement(s,p,o))
        # a bit unreliable... assumes filesystem is encoded in utf-8
        path = os.path.abspath(self.path)
        fileNode = RDF.Node(RDF.Uri('file://' + path))
        add(model, fileNode, rdfNS['type'], libNS['IlluminaResult'])
        add_lit(model, fileNode, libNS['flowcell_id'], self.flowcell)
        add_lit(model, fileNode, libNS['lane_number'], self.lane)
        if self.read is not None:
            add_lit(model, fileNode, libNS['read'], self.read)
        else:
            add_lit(model, fileNode, libNS['read'], '')

        add_lit(model, fileNode, libNS['library_id'], self.project)
        add_lit(model, fileNode, libNS['multiplex_index'], self.index)
        add_lit(model, fileNode, libNS['split_id'], self.split)
        add_lit(model, fileNode, libNS['cycle'], self.cycle)
        add_lit(model, fileNode, libNS['passed_filter'], self.pf)
        add(model, fileNode, libNS['file_type'], libNS[self.filetype])

        if base_url is not None:
            flowcell = RDF.Node(RDF.Uri("{base}/flowcell/{flowcell}/".format(
                base=base_url,
                flowcell=self.flowcell)))
            add(model, fileNode, libNS['flowcell'], flowcell)
            if self.project is not None:
                library = RDF.Node(RDF.Uri("{base}/library/{library}".format(
                    base=base_url,
                    library=self.project)))
                add(model, fileNode, libNS['library'], library)


    @classmethod
    def load_from_model(cls, model, seq_id):
        def get(s, p):
            values = []
            stmts = model.find_statements(RDF.Statement(s, p, None))
            for s in stmts:
                obj = s.object
                if not obj.is_resource():
                    values.append(fromTypedNode(obj))
                else:
                    values.append(obj)
            return values
        def get_one(s, p):
            values = get(s, p)
            if len(values) > 1:
                errmsg = u"To many values for %s %s"
                raise ValueError(errmsg % (unicode(s), unicode(p)))
            elif len(values) == 1:
                return values[0]
            else:
                return None

        if not isinstance(seq_id, RDF.Node):
            seq_id = RDF.Node(RDF.Uri(seq_id))
        result_statement = RDF.Statement(seq_id,
                                         rdfNS['type'],
                                         libNS['IlluminaResult'])
        if not model.contains_statement(result_statement):
            raise KeyError(u"%s not found" % (unicode(seq_id),))

        seq_type_node = model.get_target(seq_id, libNS['file_type'])
        seq_type = strip_namespace(libNS, seq_type_node)

        path = urlparse(str(seq_id.uri)).path
        flowcellNode = get_one(seq_id, libNS['flowcell'])
        flowcell = get_one(seq_id, libNS['flowcell_id'])
        lane = get_one(seq_id, libNS['lane_number'])
        read = get_one(seq_id, libNS['read'])

        obj = cls(seq_type, path, flowcell, lane)
        obj.read = read if read != '' else None
        obj.project = get_one(seq_id, libNS['library_id'])
        obj.index = get_one(seq_id, libNS['multiplex_index'])
        obj.split = get_one(seq_id, libNS['split_id'])
        obj.cycle = get_one(seq_id, libNS['cycle'] )
        obj.pf = get_one(seq_id, libNS['passed_filter'])
        obj.libraryNode = get_one(seq_id, libNS['library'])
        return obj


def get_flowcell_cycle(path):
    """
    Extract flowcell, cycle from pathname
    """
    path = os.path.normpath(path)
    project = None
    rest, tail = os.path.split(path)
    if tail.startswith('Project_'):
        # we're in a multiplexed sample
        project = tail
        rest, cycle = os.path.split(rest)
    else:
        cycle = tail

    rest, flowcell = os.path.split(rest)
    cycle_match = re.match("C(?P<start>[0-9]+)-(?P<stop>[0-9]+)", cycle)
    if cycle_match is None:
        raise ValueError(
            "Expected .../flowcell/cycle/ directory structure in %s" % \
            (path,))
    start = cycle_match.group('start')
    if start is not None:
        start = int(start)
    stop = cycle_match.group('stop')
    if stop is not None:
        stop = int(stop)

    return FlowcellPath(flowcell, start, stop, project)

def parse_srf(path, filename):
    flowcell_dir, start, stop, project = get_flowcell_cycle(path)
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    flowcell = records[4]
    lane = records[5][0]
    fullpath = os.path.join(path, filename)

    if flowcell_dir != flowcell:
        LOGGER.warn("flowcell %s found in wrong directory %s" % \
                         (flowcell, path))

    return SequenceFile('srf', fullpath, flowcell, lane, cycle=stop)

def parse_qseq(path, filename):
    flowcell_dir, start, stop, project = get_flowcell_cycle(path)
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    fullpath = os.path.join(path, filename)
    flowcell = records[4]
    lane = records[5][1]
    read = int(records[6][1])

    if flowcell_dir != flowcell:
        LOGGER.warn("flowcell %s found in wrong directory %s" % \
                         (flowcell, path))

    return SequenceFile('qseq', fullpath, flowcell, lane, read, cycle=stop)

def parse_fastq(path, filename):
    """Parse fastq names
    """
    flowcell_dir, start, stop, project = get_flowcell_cycle(path)
    basename = re.sub('\.fastq(\.gz|\.bz2)?$', '', filename)
    records = basename.split('_')
    fullpath = os.path.join(path, filename)
    if project is not None:
        # demultiplexed sample!
        flowcell = flowcell_dir
        lane = records[2][-1]
        read = int(records[3][-1])
        pf = True # as I understand it hiseq runs toss the ones that fail filter
        index = records[1]
        project_id = records[0]
        split = records[4]
        sequence_type = 'split_fastq'
    else:
        flowcell = records[4]
        lane = records[5][1]
        read = int(records[6][1])
        pf = parse_fastq_pf_flag(records)
        index = None
        project_id = None
        split = None
        sequence_type = 'fastq'

    if flowcell_dir != flowcell:
        LOGGER.warn("flowcell %s found in wrong directory %s" % \
                         (flowcell, path))

    return SequenceFile(sequence_type, fullpath, flowcell, lane, read,
                        pf=pf,
                        cycle=stop,
                        project=project_id,
                        index=index,
                        split=split)

def parse_fastq_pf_flag(records):
    """Take a fastq filename split on _ and look for the pass-filter flag
    """
    if len(records) < 8:
        pf = None
    else:
        fastq_type = records[-1].lower()
        if fastq_type.startswith('pass'):
            pf = True
        elif fastq_type.startswith('nopass'):
            pf = False
        elif fastq_type.startswith('all'):
            pf = None
        else:
            raise ValueError("Unrecognized fastq name: %s" % (
                "_".join(records),))

    return pf

def parse_eland(path, filename, eland_match=None):
    if eland_match is None:
        eland_match = eland_re.match(filename)
    fullpath = os.path.join(path, filename)
    flowcell, start, stop, project = get_flowcell_cycle(path)
    if eland_match.group('lane'):
        lane = eland_match.group('lane')
    else:
        lane = None
    if eland_match.group('read'):
        read = int(eland_match.group('read'))
    else:
        read = None
    return SequenceFile('eland', fullpath, flowcell, lane, read, cycle=stop)

def scan_for_sequences(dirs):
    """
    Scan through a list of directories for sequence like files
    """
    sequences = []
    if type(dirs) in types.StringTypes:
        raise ValueError("You probably want a list or set, not a string")

    for d in dirs:
        LOGGER.info("Scanning %s for sequences" % (d,))
        if not os.path.exists(d):
            LOGGER.warn("Flowcell directory %s does not exist" % (d,))
            continue

        for path, dirname, filenames in os.walk(d):
            for f in filenames:
                seq = None
                # find sequence files
                if f.endswith('.md5'):
                    continue
                elif f.endswith('.srf') or f.endswith('.srf.bz2'):
                    seq = parse_srf(path, f)
                elif qseq_re.match(f):
                    seq = parse_qseq(path, f)
                elif f.endswith('.fastq') or \
                     f.endswith('.fastq.bz2') or \
                     f.endswith('.fastq.gz'):
                    seq = parse_fastq(path, f)
                eland_match = eland_re.match(f)
                if eland_match:
                    if f.endswith('.md5'):
                        continue
                    seq = parse_eland(path, f, eland_match)
                if seq:
                    sequences.append(seq)
                    LOGGER.debug("Found sequence at %s" % (f,))

    return sequences


def update_model_sequence_library(model, base_url):
    """Find sequence objects and add library information if its missing
    """
    file_body = """
    prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>
    select ?filenode ?flowcell_id ?lane_id ?library_id ?flowcell ?library
    where {
       ?filenode a libns:IlluminaResult ;
                 libns:flowcell_id ?flowcell_id ;
                 libns:lane_number ?lane_id .
       OPTIONAL { ?filenode libns:flowcell ?flowcell . }
       OPTIONAL { ?filenode libns:library ?library .}
       OPTIONAL { ?filenode libns:library_id ?library_id .}
    }
    """
    LOGGER.debug("update_model_sequence_library query %s", file_body)
    file_query = RDF.SPARQLQuery(file_body)
    files = file_query.execute(model)

    libraryNS = RDF.NS(urljoin(base_url, 'library/'))
    flowcellNS = RDF.NS(urljoin(base_url, 'flowcell/'))
    for f in files:
        filenode = f['filenode']
        LOGGER.debug("Updating file node %s", str(filenode))
        lane_id = fromTypedNode(f['lane_id'])
        if f['flowcell'] is None:
            flowcell = flowcellNS[str(f['flowcell_id'])+'/']
            LOGGER.debug("Adding file (%s) to flowcell (%s) link",
                         str(filenode),
                         str(flowcell))
            model.add_statement(
                RDF.Statement(filenode, libNS['flowcell'], flowcell))
        else:
            flowcell = f['flowcell']

        if f['library'] is None:
            if f['library_id'] is not None:
                library = libraryNS[str(f['library_id']) + '/']
            else:
                library = guess_library_from_model(model, base_url,
                                                   flowcell,
                                                   lane_id)
                if library is None:
                    LOGGER.error("Unable to decypher: %s %s",
                                 str(flowcell), str(lane_id))
                    continue
                library_id = toTypedNode(simplify_uri(library))
                LOGGER.debug("Adding file (%s) to library (%s) link",
                             str(filenode),
                             str(library))
                model.add_statement(
                    RDF.Statement(filenode, libNS['library_id'], library_id))
            if library is not None:
                model.add_statement(
                    RDF.Statement(filenode, libNS['library'], library))


def guess_library_from_model(model, base_url, flowcell, lane_id):
    """Attempt to find library URI
    """
    flowcellNode = RDF.Node(flowcell)
    flowcell = str(flowcell.uri)
    lane_body = """
    prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>
    prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix xsd: <http://www.w3.org/2001/XMLSchema#>

    select ?library ?lane
    where {{
      <{flowcell}> libns:has_lane ?lane ;
                   a libns:IlluminaFlowcell .
      ?lane libns:lane_number ?lane_id ;
            libns:library ?library .
      FILTER(str(?lane_id) = "{lane_id}")
    }}
    """
    lane_body = lane_body.format(flowcell=flowcell, lane_id=lane_id)
    LOGGER.debug("guess_library_from_model: %s", lane_body)
    lanes = []
    tries = 3
    while len(lanes) == 0 and tries > 0:
        tries -= 1
        lane_query = RDF.SPARQLQuery(lane_body)
        lanes = [ l for l in lane_query.execute(model)]
        if len(lanes) > 1:
            # CONFUSED!
            errmsg = "Too many libraries for flowcell {flowcell} "\
                     "lane {lane} = {count}"
            LOGGER.error(errmsg.format(flowcell=flowcell,
                                       lane=lane_id,
                                       count=len(lanes)))
            return None
        elif len(lanes) == 1:
            # success
            return lanes[0]['library']
        else:
            # try grabbing data
            model.load(flowcellNode.uri, name="rdfa")
