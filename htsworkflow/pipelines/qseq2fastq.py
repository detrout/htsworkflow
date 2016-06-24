#!/usr/bin/env python
"""Convert a collection of qseq or a tar file of qseq files to a fastq file
"""
from __future__ import print_function, unicode_literals
from glob import glob
import os
from optparse import OptionParser
import numpy
import sys
import tarfile

from htsworkflow.util.version import version
from htsworkflow.util.conversion import parse_slice
from htsworkflow.pipelines.desplit_fastq import open_output


def main(cmdline=None):
    """Command line driver: [None, '-i', 'tarfile', '-o', 'target.fastq']
    """
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.version:
        print(version())
        return 0

    if opts.infile is not None:
        qseq_generator = tarfile_generator(opts.infile)
    elif len(args) > 0:
        qseq_generator = file_generator(args)
    else:
        qseq_generator = [sys.stdin]

    if opts.output is not None:
        output = open_output(opts.output, opts)
    else:
        output = sys.stdout

    if opts.nopass_output is not None:
        nopass_output = open_output(opts.nopass_output, opts)
    else:
        nopass_output = None

    qseq_parser = Qseq2Fastq(qseq_generator, output, nopass_output)
    qseq_parser.fastq = not opts.fasta
    qseq_parser.flowcell_id = opts.flowcell
    qseq_parser.trim = parse_slice(opts.slice)
    qseq_parser.reportFilter = opts.pf

    qseq_parser.run()


def make_parser():
    """Return option parser"""
    usage = "%prog: [options] *_qseq.txt\nProduces Phred33 files by default"
    parser = OptionParser(usage)
    parser.add_option("-a", "--fasta", default=False, action="store_true",
                      help="produce fasta files instead of fastq files")
    parser.add_option("-f", "--flowcell", default=None,
                      help="Set flowcell ID for output file")
    parser.add_option("-i", "--infile", default=None,
                      help='source tar file (if reading from an archive '\
                           'instead of a directory)')
    parser.add_option("-o", "--output", default=None,
                      help="output fastq file")
    parser.add_option("-n", "--nopass-output", default=None,
                      help="if provided send files that failed "\
                           "illumina filter to a differentfile")
    parser.add_option("-s", "--slice",
                      help="specify python slice, e.g. 0:75, 0:-1",
                      default=None)
    parser.add_option("--pf", help="report pass filter flag", default=False,
                      action="store_true")
    parser.add_option('--gzip', default=False, action='store_true',
                      help='gzip output')
    parser.add_option('--bzip', default=False, action='store_true',
                      help='bzip output')
    parser.add_option("--version", default=False, action="store_true",
                      help="report software version")

    return parser


def file_generator(pattern_list):
    """Given a list of glob patterns yield open streams for matching files"""
    for pattern in pattern_list:
        for filename in glob(pattern):
            # this needs to return bytes, because tarfile generate does
            yield open(filename, "rb")


def tarfile_generator(tarfilename):
    """Yield open streams for files inside a tarfile"""
    archive = tarfile.open(tarfilename, 'r|*')
    for tarinfo in archive:
        yield archive.extractfile(tarinfo)


class Qseq2Fastq(object):
    """
    Convert qseq files to fastq (or fasta) files.
    """
    def __init__(self, sources, pass_destination, nopass_destination=None):
        self.sources = sources
        self.pass_destination = pass_destination
        if nopass_destination is not None:
            self.nopass_destination = nopass_destination
        else:
            self.nopass_destination = pass_destination

        self.fastq = True
        self.flowcell_id = None
        self.trim = slice(None)
        self.report_filter = False

    def _format_flowcell_id(self):
        """
        Return formatted flowcell ID
        """
        if self.flowcell_id is not None:
            return self.flowcell_id + "_"
        else:
            return ""

    def run(self):
        """Run conversion
        (Used to match threading/multiprocessing API)
        """
        if self.fastq:
            header_template = '@'
        else:
            # fasta case
            header_template = '>'
        header_template += self._format_flowcell_id() + \
                           '%s_%s:%s:%s:%s:%s/%s%s%s'

        for qstream in self.sources:
            for line in qstream:
                # parse line
                record = line.decode('ascii').rstrip().split('\t')
                machine_name = record[0]
                run_number = record[1]
                lane_number = record[2]
                tile = record[3]
                x = record[4]
                y = record[5]
                #index = record[6]
                read = record[7]
                sequence = record[8].replace('.', 'N')
                quality = convert_illumina_quality(record[9])

                # add pass qc filter if we want it
                pass_qc = int(record[10])
                if self.report_filter:
                    pass_qc_msg = " pf=%s" % (pass_qc)
                else:
                    pass_qc_msg = ""

                header = header_template % ( \
                    machine_name,
                    run_number,
                    lane_number,
                    tile,
                    x,
                    y,
                    read,
                    pass_qc_msg,
                    os.linesep)

                # if we passed the filter write to the "good" file
                if pass_qc:
                    destination = self.pass_destination
                else:
                    destination = self.nopass_destination

                destination.write(header)
                destination.write(sequence[self.trim])
                destination.write(os.linesep)
                if self.fastq:
                    destination.write('+')
                    destination.write(os.linesep)
                    destination.write(quality[self.trim].tobytes().decode('ascii'))
                    destination.write(os.linesep)

def convert_illumina_quality(illumina_quality):
    """Convert an Illumina quality score to a Phred ASCII quality score.
    """
    # Illumina scores are Phred + 64
    # Fastq scores are Phread + 33
    # the following code grabs the string, converts to short ints and
    # subtracts 31 (64-33) to convert between the two score formats.
    # The numpy solution is twice as fast as some of my other
    # ideas for the conversion.
    # sorry about the uglyness in changing from character, to 8-bit int
    # and back to a character array
    quality = numpy.asarray(illumina_quality, 'c')
    quality.dtype = numpy.uint8
    quality -= 31
     # I'd like to know what the real numpy char type is
    quality.dtype = '|S1'
    return quality


if __name__ == "__main__":
    main()
