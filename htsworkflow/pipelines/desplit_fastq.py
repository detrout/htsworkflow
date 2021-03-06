#!/usr/bin/env python
"""Write fastq data from multiple compressed files into a single file
"""
import bz2
import gzip
from glob import glob
import os
from optparse import OptionParser
import sys

from htsworkflow.util.version import version
from htsworkflow.util.opener import autoopen, isurllike
from htsworkflow.util.conversion import parse_slice

SEQ_HEADER = 0
SEQUENCE = 1
QUAL_HEADER = 2
QUALITY = 3
INVALID = -1


def main(cmdline=None):
    """Command line driver: [None, 'option', '*.fastq.bz2']
    """
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.version:
        print (version())
        return 0

    if opts.output is not None:
        output = open_output(opts.output, opts)
    else:
        output = sys.stdout

    desplitter = DesplitFastq(file_generator(args), output)
    desplitter.trim = parse_slice(opts.slice)
    desplitter.run()

    return 0


def make_parser():
    """Generate an option parser for above main function"""

    usage = '%prog: [options] *.fastq.gz'
    parser = OptionParser(usage)

    parser.add_option('-o', '--output', default=None,
                      help='output fastq file')
    parser.add_option('-s', '--slice',
                      help="specify python slice, e.g. 0:75, 0:-1",
                      default=None)
    parser.add_option('--gzip', default=False, action='store_true',
                      help='gzip output')
    parser.add_option('--bzip', default=False, action='store_true',
                      help='bzip output')
    parser.add_option("--version", default=False, action="store_true",
                      help="report software version")
    return parser


def open_output(output, opts):
    """Open output file with right compression library
    """
    if opts.bzip:
        return bz2.open(output, 'wt')
    elif opts.gzip:
        return gzip.open(output, 'wt')
    else:
        return open(output, 'w')


def file_generator(pattern_list):
    """Given a list of glob patterns return decompressed streams
    """
    for pattern in pattern_list:
        if isurllike(pattern, 'rt'):
            yield autoopen(pattern, 'rt')
        else:
            for filename in glob(pattern):
                yield autoopen(filename, 'rt')


class DesplitFastq(object):
    """Merge multiple fastq files into a single file"""
    def __init__(self, sources, destination):
        self.sources = sources
        self.destination = destination

        self.making_fastq = True
        self.trim = slice(None)

    def run(self):
        """Do the conversion

        This is here so we can run via threading/multiprocessing APIs
        """
        state = SEQ_HEADER
        files_read = 0
        for stream in self.sources:
            files_read += 1
            for line in stream:
                line = line.rstrip()
                if state == SEQ_HEADER:
                    self.destination.write(line)
                    state = SEQUENCE
                elif state == SEQUENCE:
                    self.destination.write(line[self.trim])
                    state = QUAL_HEADER
                elif state == QUAL_HEADER:
                    self.destination.write(line)
                    state = QUALITY
                elif state == QUALITY:
                    self.destination.write(line[self.trim])
                    state = SEQ_HEADER
                self.destination.write(os.linesep)

        if files_read == 0:
            raise RuntimeError("No files processed")

if __name__ == "__main__":
    main()
