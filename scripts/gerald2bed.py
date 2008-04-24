#!/usr/bin/python
"""
Convert a group of eland_result files from a sequencer run to bed files.
"""
from glob import glob
import logging
import optparse
import sys
import os

from gaworkflow.util.makebed import make_bed_from_eland_stream, make_description

def make_bed_for_gerald(eland_dir, output_dir, prefix, database, flowcell):
    """
    convert s_[1-8]_eland_result.txt to corresponding bed files
    """
    eland_files = glob(os.path.join(eland_dir, 's_[1-8]_eland_result.txt'))
    out_files = glob(os.path.join(eland_dir, 's_[1-8]_eland_result.bed'))
    if len(out_files) > 0:
        raise RuntimeError("please move old bedfiles")

    logging.info('Processing %s using flowcell id %s' % (eland_dir, flowcell))
    for pathname in eland_files:
        path, name = os.path.split(pathname)
        lane = int(name[2])
        outname = 's_%d_eland_result.bed' %(lane,)
        logging.info('Converting lane %d to %s' % (lane, outname))

        outpathname = os.path.join(eland_dir, outname)
        # look up descriptions
        bed_name, description = make_description(database, flowcell, lane)

        # open files
        instream = open(pathname,'r')
        outstream = open(outpathname,'w')

        make_bed_from_eland_stream(
          instream, outstream, name, description, prefix
        )

def make_parser():
  usage = """%prog: --flowcell <flowcell id> directory_name

directory should contain a set of 8 eland result files named like
s_[12345678]_eland_result.txt"""


  parser = optparse.OptionParser(usage)

  parser.add_option('-o', '--output', dest='output',
                    help="destination directory for our bed files" \
                         "defaults to eland directory",
                    default=None)
  parser.add_option('--chromosome', dest='prefix',
                    help='Set the chromosome prefix name. defaults to "chr"',
                    default='chr')
  parser.add_option("--database", dest='database',
                    help="specify location of fctracker database",
                    default=None)
  parser.add_option("--flowcell", dest='flowcell',
                    help="specify the flowcell id for this run",
                    default=None)
  parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                    help='increase verbosity',
                    default=False)
  return parser

def main(command_line=None):
    logging.basicConfig(level=logging.WARNING)
    if command_line is None:
        command_line = sys.argv[1:]

    parser = make_parser()
    (opts, args) = parser.parse_args(command_line)

    if len(args) != 1:
        parser.error('Directory name required')

    eland_dir = args[0]
    if not os.path.isdir(eland_dir):
        parser.error('%s must be a directory' % (eland_dir,))

    if opts.flowcell is None:
        parser.error('Flowcell ID required')

    if opts.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

    make_bed_for_gerald(eland_dir, opts.output, opts.prefix, opts.database, opts.flowcell)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

