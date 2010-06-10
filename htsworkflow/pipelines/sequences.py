"""
Utilities to work with the various eras of sequence archive files
"""
import logging
import os
import re

eland_re = re.compile('s_(?P<lane>\d)(_(?P<read>\d))?_eland_')
raw_seq_re = re.compile('woldlab_[0-9]{6}_[^_]+_[\d]+_[\dA-Z]+')
qseq_re = re.compile('woldlab_[0-9]{6}_[^_]+_[\d]+_[\dA-Z]+_l[\d]_r[\d].tar.bz2')

class SequenceFile(object):
    """
    Simple container class that holds the path to a sequence archive
    and basic descriptive information.     
    """
    def __init__(self, filetype, path, flowcell, lane, read=None, pf=None, cycle=None):
        self.filetype = filetype
        self.path = path
        self.flowcell = flowcell
        self.lane = lane
        self.read = read
        self.pf = pf
        self.cycle = cycle

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
        attributes = ['filetype','flowcell', 'lane', 'read', 'pf', 'cycle']
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
        
def parse_srf(path, filename):
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    flowcell = records[4]
    lane = int(records[5][0])
    fullpath = os.path.join(path, filename)
    return SequenceFile('srf', fullpath, flowcell, lane)

def parse_qseq(path, filename):
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    fullpath = os.path.join(path, filename)
    flowcell = records[4]
    lane = int(records[5][1])
    read = int(records[6][1])
    return SequenceFile('qseq', fullpath, flowcell, lane, read)

def parse_fastq(path, filename):
    basename, ext = os.path.splitext(filename)
    records = basename.split('_')
    fullpath = os.path.join(path, filename)
    flowcell = records[4]
    lane = int(records[5][1])
    read = int(records[6][1])
    if records[-1].startswith('pass'):
        pf = True
    elif records[-1].startswith('nopass'):
        pf = False
    else:
        raise ValueError("Unrecognized fastq name")
        
    return SequenceFile('fastq', fullpath, flowcell, lane, read, pf=pf)

def parse_eland(path, filename, eland_match=None):
    if eland_match is None:
        eland_match = eland_re.match(filename)
    fullpath = os.path.join(path, filename)
    rest, cycle = os.path.split(path)
    rest, flowcell = os.path.split(rest)
    if eland_match.group('lane'):
        lane = int(eland_match.group('lane'))
    else:
        lane = None
    if eland_match.group('read'):
        read = int(eland_match.group('read'))
    else:
        read = None
    return SequenceFile('eland', fullpath, flowcell, lane, read, cycle=cycle)
    
def scan_for_sequences(dirs):
    """
    Scan through a list of directories for sequence like files
    """
    # be forgiving if someone just gives us a string
    if type(dirs) != type([]):
        dirs = [dirs]

    sequences = []
    for d in dirs:
        logging.info("Scanning %s for sequences" % (d,))
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
                    elif f.endswith('fastq') or f.endswith('.fastq.bz2'):
                        seq = parse_fastq(path, f)
                eland_match = eland_re.match(f)
                if eland_match:
                    if f.endswith('.md5'):
                        continue
                    seq = parse_eland(path, f, eland_match)
                if seq:
                    sequences.append(seq)
                    logging.debug("Found sequence at %s" % (f,))
                    
    return sequences
