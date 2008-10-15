#!/usr/bin/env python

import logging
from optparse import OptionParser
import os
import subprocess
import sys

from htsworkflow.pipeline import gerald
from htsworkflow.pipeline import runfolder

def make_query_filename(eland_obj, output_dir):
    query_name = '%s_%s_eland_query.txt' 
    query_name %= (eland_obj.sample_name, eland_obj.lane_id)

    query_pathname = os.path.join(output_dir, query_name)
    
    if os.path.exists(query_pathname):
        logging.warn("overwriting %s" % (query_pathname,))

    return query_pathname

def make_result_filename(eland_obj, output_dir):
    result_name = '%s_%s_eland_result.txt' 
    result_name %= (eland_obj.sample_name, eland_obj.lane_id)

    result_pathname = os.path.join(output_dir, result_name)
    
    if os.path.exists(result_pathname):
        logging.warn("overwriting %s" % (result_pathname,))

    return result_pathname

def extract_sequence(inpathname, query_pathname, length, dry_run=False):
    logging.info('extracting %d bases' %(length,))
    logging.info('extracting from %s' %(inpathname,))
    logging.info('extracting to %s' %(query_pathname,))
    
    if not dry_run: 
        try:
            instream = open(inpathname, 'r')
            outstream = open(query_pathname, 'w')
            gerald.extract_eland_sequence(instream, outstream, 0, length)
        finally:
            outstream.close()
            instream.close()
    
def run_eland(length, query_name, genome, result_name, multi=False, dry_run=False):
    cmdline = ['eland_%d' % (length,), query_name, genome, result_name]
    if multi:
        cmdline += ['--multi']

    logging.info('running eland: ' + " ".join(cmdline))
    if not dry_run:
        return subprocess.Popen(cmdline)
    else:
        return None


def rerun(gerald_dir, output_dir, length=25, dry_run=False):
    """
    look for eland files in gerald_dir and write a subset to output_dir
    """
    logging.info("Extracting %d bp from files in %s" % (length, gerald_dir))
    g = gerald.gerald(gerald_dir)

    # this will only work if we're only missing the last dir in output_dir
    if not os.path.exists(output_dir):
        logging.info("Making %s" %(output_dir,))
        if not dry_run: os.mkdir(output_dir)

    processes = []
    for lane_id, lane_param in g.lanes.items():
        eland = g.eland_results[lane_id]

        inpathname = eland.pathname
        query_pathname = make_query_filename(eland, output_dir)
        result_pathname = make_result_filename(eland, output_dir)

        extract_sequence(inpathname, query_pathname, length, dry_run=dry_run)

        p = run_eland(length, 
                      query_pathname, 
                      lane_param.eland_genome, 
                      result_pathname, 
                      dry_run=dry_run)
        if p is not None:
            processes.append(p)

    for p in processes:
        p.wait()
        
def make_parser():
    usage = '%prog: [options] runfolder'

    parser = OptionParser(usage)
    
    parser.add_option('--gerald', 
                      help='specify location of GERALD directory',
                      default=None)
    parser.add_option('-o', '--output',
                      help='specify output location of files',
                      default=None)
    parser.add_option('-l', '--read-length', type='int',
                      help='specify new eland length',
                      dest='length',
                      default=25)
    parser.add_option('--dry-run', action='store_true',
                      help='only pretend to run',
                      default=False)
    parser.add_option('-v', '--verbose', action='store_true',
                      help='increase verbosity',
                      default=False)

    return parser


def main(cmdline=None):
    logging.basicConfig(level=logging.WARNING)

    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.length < 16 or opts.length > 32:
        parser.error("eland can only process reads in the range 16-32")

    if len(args) > 1:
        parser.error("Can only process one runfolder directory")
    elif len(args) == 1:
        runs = runfolder.get_runs(args[0])
        if len(runs) != 1:
            parser.error("Not a runfolder")
        opts.gerald = runs[0].gerald.pathname
        if opts.output is None:
            opts.output = os.path.join(
                runs[0].pathname, 
                'Data', 
                # pythons 0..n ==> elands 1..n+1
                'C1-%d' % (opts.length+1,) 
            )

    elif opts.gerald is None:
        parser.error("need gerald directory")
    
    if opts.output is None:
        parser.error("specify location for the new eland files")

    if opts.verbose:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

    rerun(opts.gerald, opts.output, opts.length, dry_run=opts.dry_run)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
