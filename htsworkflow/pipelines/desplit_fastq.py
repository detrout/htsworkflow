#!/usr/bin/env python
"""Write fastq data from multiple compressed files into a single file
"""

from glob import glob
import os
from optparse import OptionParser
import sys

from htsworkflow.util.version import version
from htsworkflow.util.opener import autoopen
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
        output = open(opts.output, 'w')
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
    parser.add_option("--version", default=False, action="store_true",
                      help="report software version")
    return parser


def file_generator(pattern_list):
    """Given a list of glob patterns return decompressed streams
    """
    for pattern in pattern_list:
        for filename in glob(pattern):
            yield autoopen(filename, 'r')


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
        for stream in self.sources:
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


if __name__ == "__main__":
    main()
