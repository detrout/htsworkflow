"""
Utilities to work with the various eras of sequence archive files
"""
import logging
import os
import re

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

class SequenceFile(object):
    """
    Simple container class that holds the path to a sequence archive
    and basic descriptive information.
    """
    def __init__(self, filetype, path, flowcell, lane, read=None, pf=None, cycle=None,
                 project=None,
                 index=None):
        self.filetype = filetype
        self.path = path
        self.flowcell = flowcell
        self.lane = lane
        self.read = read
        self.pf = pf
        self.cycle = cycle
        self.project = project
        self.index = index

    def __hash__(self):
        return hash(self.key())

    def key(self):
        return (self.flowcell, self.lane)

    def unicode(self):
        return unicode(self.path)

    def __eq__(self, other):
        """
        Equality is defined if everything but the path matches
        """
        attributes = ['filetype','flowcell', 'lane', 'read', 'pf', 'cycle', 'project', 'index']
        for a in attributes:
            if getattr(self, a) != getattr(other, a):
                return False

        return True

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

    def save(self, cursor):
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

def get_flowcell_cycle(path):
    """
    Extract flowcell, cycle from pathname
    """
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

    return flowcell, start, stop, project

def parse_srf(path, filename):
    flowcell_dir, start, stop, project = get_flowcell_cycle(path)
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    flowcell = records[4]
    lane = int(records[5][0])
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
    lane = int(records[5][1])
    read = int(records[6][1])

    if flowcell_dir != flowcell:
        LOGGER.warn("flowcell %s found in wrong directory %s" % \
                         (flowcell, path))

    return SequenceFile('qseq', fullpath, flowcell, lane, read, cycle=stop)

def parse_fastq(path, filename):
    """Parse fastq names
    """
    flowcell_dir, start, stop, project = get_flowcell_cycle(path)
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    fullpath = os.path.join(path, filename)
    if project is not None:
        # demultiplexed sample!
        flowcell = flowcell_dir
        lane = int(records[2][-1])
        read = int(records[3][-1])
        pf = True # as I understand it hiseq runs toss the ones that fail filter
        index = records[1]
        project_id = records[0]
    else:
        flowcell = records[4]
        lane = int(records[5][1])
        read = int(records[6][1])
        pf = parse_fastq_pf_flag(records)
        index = None
        project_id = None

    if flowcell_dir != flowcell:
        LOGGER.warn("flowcell %s found in wrong directory %s" % \
                         (flowcell, path))

    return SequenceFile('fastq', fullpath, flowcell, lane, read,
                        pf=pf,
                        cycle=stop,
                        project=project_id,
                        index=index)

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
            raise ValueError("Unrecognized fastq name %s at %s" % \
                             (records[-1], os.path.join(path,filename)))

    return pf

def parse_eland(path, filename, eland_match=None):
    if eland_match is None:
        eland_match = eland_re.match(filename)
    fullpath = os.path.join(path, filename)
    flowcell, start, stop, project = get_flowcell_cycle(path)
    if eland_match.group('lane'):
        lane = int(eland_match.group('lane'))
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
    for d in dirs:
        LOGGER.info("Scanning %s for sequences" % (d,))
        if not os.path.exists(d):
            LOGGER.warn("Flowcell directory %s does not exist" % (d,))
            continue

        for path, dirname, filenames in os.walk(d):
            for f in filenames:
                seq = None
                # find sequence files
                if raw_seq_re.match(f):
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
