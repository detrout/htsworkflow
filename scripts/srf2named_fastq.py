#!/usr/bin/env python
import logging
from optparse import OptionParser
import os
from subprocess import Popen, PIPE
import sys

from htsworkflow.util.opener import autoopen


def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if len(args) != 1:
        parser.error("Requires one argument")

    if opts.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARN)

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
        source = srf_open(args[0], opts.cnf1)
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
    parser.add_option('-c','--cnf1',default=False, action="store_true",
      help="pass -c to srf2fastq, needed for calibrated quality values"
    )
    parser.add_option('--force', default=False, action="store_true",
                      help="overwrite existing files.")
    parser.add_option('--flowcell', default=None,
                      help="add flowcell id header to sequence")
    parser.add_option('-l','--left', default="r1.fastq",
                      help='left side filename')
    parser.add_option('-r','--right', default="r2.fastq",
                      help='right side filename')
    parser.add_option('-m','--mid', default=None, 
                      help='actual sequence mid point')
    parser.add_option('-s','--single', default=None,
                      help="single fastq target name")
    parser.add_option('-v', '--verbose', default=False, action="store_true",
                      help="show information about what we're doing.")
    return parser


def srf_open(filename, cnf1=False):
    """
    Make a stream from srf file using srf2fastq
    """
    
    cmd = ['srf2fastq']
    if cnf1:
        cmd.append('-c')
    cmd.append(filename)
      
    logging.info('srf command: %s' % (" ".join(cmd),))
    p = Popen(cmd, stdout=PIPE)
    return p.stdout
    

def convert_single_to_fastq(instream, target1, header=''):
    for line in instream:
        # sequence header
        if line[0] == '@':
            line = line.strip()
            target1.write('@')
            target1.write(header)
            target1.write(line[1:])
            target1.write(os.linesep)

        # quality header
        elif line[0] == '+':
            target1.write(line)
        # sequence or quality data
        else:
            target1.write(line)
        
def convert_single_to_two_fastq(instream, target1, target2, mid=None, header=''):
    if mid is not None:
        mid = int(mid)

    for line in instream:
        # sequence header
        if line[0] == '@':
            line = line.strip()
            target1.write('@')
            target1.write(header)
            target1.write(line[1:])
            target1.write("/1")
            target1.write(os.linesep)

            target2.write('@')
            target2.write(header)
            target2.write(line[1:])
            target2.write("/2")
            target2.write(os.linesep)

        # quality header
        elif line[0] == '+':
            target1.write(line)
            target2.write(line)
        # sequence or quality data
        else:
            line = line.strip()
            if mid is None:
                mid = len(line)/2
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
