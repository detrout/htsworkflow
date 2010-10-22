#!/usr/bin/env python
import logging
import mmap
from optparse import OptionParser
import os
from subprocess import Popen, PIPE
import sys

from htsworkflow.util.opener import autoopen
from htsworkflow.version import version

# constants for our fastq finite state machine
FASTQ_HEADER = 0
FASTQ_SEQUENCE = 1
FASTQ_SEQUENCE_HEADER = 2
FASTQ_QUALITY = 3

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARN)

    if opts.version:
        print version()
        return 0

    if len(args) != 1:
        parser.error("Requires one argument, got: %s" % (str(args)))

    if opts.flowcell is not None:
        header = "%s_" % (opts.flowcell,)
    else:
        header = ''

    if opts.single:
        left = open_write(opts.single, opts.force)
    else:
        left = open_write(opts.left, opts.force)
        right = open_write(opts.right, opts.force)
    
    # open the srf, fastq, or compressed fastq
    if is_srf(args[0]):
        source = srf_open(args[0])
    else:
        source = autoopen(args[0])

    if opts.single:
        convert_single_to_fastq(source, left, header)
    else:
        convert_single_to_two_fastq(source, left, right, opts.mid, header)
   
    return 0

def make_parser():
    parser = OptionParser("""%prog: [options] file

file can be either a fastq file or a srf file.
You can also force the flowcell ID to be added to the header.""")

    parser.add_option('--force', default=False, action="store_true",
                      help="overwrite existing files.")
    parser.add_option('--flowcell', default=None,
                      help="add flowcell id header to sequence")
    parser.add_option('-l','--left', default="r1.fastq",
                      help='left side filename')
    parser.add_option('-m','--mid', default=None, 
                      help='actual sequence mid point')
    parser.add_option('-r','--right', default="r2.fastq",
                      help='right side filename')
    parser.add_option('-s','--single', default=None,
                      help="single fastq target name")
    parser.add_option('-v', '--verbose', default=False, action="store_true",
                      help="show information about what we're doing.")
    parser.add_option('--version', default=False, action="store_true",
                      help="Report software version")
    return parser


def srf_open(filename, cnf1=False):
    """
    Make a stream from srf file using srf2fastq
    """
    cmd = ['srf2fastq']
    if is_cnf1(filename):
        cmd.append('-c')
    cmd.append(filename)
      
    logging.info('srf command: %s' % (" ".join(cmd),))
    p = Popen(cmd, stdout=PIPE)
    return p.stdout
    

def convert_single_to_fastq(instream, target1, header=''):

    state = FASTQ_HEADER
    for line in instream:
        line = line.strip()
        # sequence header
        if state == FASTQ_HEADER:
            write_header(target1, header, line)
            state = FASTQ_SEQUENCE
        # sequence
        elif state == FASTQ_SEQUENCE:
            write_sequence(target1, line)
            state = FASTQ_SEQUENCE_HEADER
        # quality header
        elif state == FASTQ_SEQUENCE_HEADER:
            # the sequence header isn't really sequence, but 
            # we're just passing it through
            write_sequence(target1, line)
            state = FASTQ_QUALITY
        # sequence or quality data
        elif state == FASTQ_QUALITY:
            write_sequence(target1, line)
            state = FASTQ_HEADER
        else:
            raise RuntimeError("Unrecognized STATE in fastq split")


        
def convert_single_to_two_fastq(instream, target1, target2, mid=None, header=''):
    """
    read a fastq file where two paired ends have been run together into 
    two halves.

    instream is the source stream
    target1 and target2 are the destination streams
    """
    if mid is not None:
        mid = int(mid)

    state = FASTQ_HEADER
    for line in instream:
        line = line.strip()
        # sequence header
        if state == FASTQ_HEADER:
            write_header(target1, header, line, "/1")
            write_header(target2, header, line, "/2")
            state = FASTQ_SEQUENCE
        # sequence
        elif state == FASTQ_SEQUENCE:
            if mid is None:
                mid = len(line)/2
            write_split_sequence(target1, target2, line, mid)
            state = FASTQ_SEQUENCE_HEADER
        # quality header
        elif state == FASTQ_SEQUENCE_HEADER:
            # the sequence header isn't really sequence, but 
            # we're just passing it through
            write_sequence(target1, line)
            write_sequence(target2, line)

            state = FASTQ_QUALITY
        # sequence or quality data
        elif state == FASTQ_QUALITY:
            write_split_sequence(target1, target2, line, mid)
            state = FASTQ_HEADER
        else:
            raise RuntimeError("Unrecognized STATE in fastq split")

def write_header(target, prefix, line, suffix=''):
    target.write('@')
    target.write(prefix)
    target.write(line[1:])
    target.write(suffix)
    target.write(os.linesep)

def write_sequence(target, line):
    target.write(line)
    target.write(os.linesep)

def write_split_sequence(target1, target2, line, mid):
    target1.write(line[:mid])
    target1.write(os.linesep)

    target2.write(line[mid:])
    target2.write(os.linesep)

def is_srf(filename):
    """
    Check filename to see if it is likely to be a SRF file
    """
    f = open(filename, 'r')
    header = f.read(4)
    f.close()
    return header == "SSRF"

def is_cnf1(filename):
    """
    Brute force detection if a SRF file is using CNF1/CNF4 records
    """
    max_header = 1024 ** 2
    PROGRAM_ID = 'PROGRAM_ID\000'
    cnf4_apps = set(("solexa2srf v1.4", 
                    "illumina2srf v1.11.5.Illumina.1.3"))

    if not is_srf(filename):
        raise ValueError("%s must be a srf file" % (filename,))

    fd = os.open(filename, os.O_RDONLY)
    f = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
    # alas the max search length requires python 2.6+
    program_id_location = f.find(PROGRAM_ID, 0) #, max_header)
    program_header_start = program_id_location+len(PROGRAM_ID)
    next_null = f.find('\000', program_header_start) #, max_header)
    program_id_header = f[program_header_start:next_null]
    f.close()
    os.close(fd)

    if program_id_header in cnf4_apps:
        return False
    else:
        return True

def open_write(filename, force=False):
    """
    Open a file, but throw an exception if it already exists
    """
    if not force:
        if os.path.exists(filename):
            raise RuntimeError("%s exists" % (filename,))

    return open(filename, 'w')

def foo():
    path, name = os.path.split(filename)
    base, ext = os.path.splitext(name)

    target1_name = base + '_r1.fastq'
    target2_name = base + '_r2.fastq'

    for target_name in [target1_name, target2_name]:
        print 'target name', target_name
        if os.path.exists(target_name):
            raise RuntimeError("%s exists" % (target_name,))

    instream = open(filename,'r')
    target1 = open(target1_name,'w')
    target2 = open(target2_name,'w')


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
