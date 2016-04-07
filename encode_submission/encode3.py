#!/usr/bin/env python
"""Create a track hub
"""
from __future__ import print_function, unicode_literals

import argparse
import logging
import os

from htsworkflow.util import api
from htsworkflow.util.rdfhelp import \
    get_model, \
    get_serializer, \
    load_into_model, \
    sparql_query
from htsworkflow.submission.daf import get_submission_uri
from htsworkflow.submission.submission import list_submissions
from htsworkflow.submission.results import ResultMap
from htsworkflow.submission.condorfastq import CondorFastqExtract
from htsworkflow.submission.aws_submission import AWSSubmission

logger = logging.getLogger(__name__)

INDENTED = "  " + os.linesep

import django
if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'htsworkflow.settings.local'

def main(cmdline=None):
    parser = make_parser()
    args = parser.parse_args(cmdline)
    submission_uri = None

    from django.conf import settings

    if args.debug:
        settings.LOGGING['loggers']['htsworkflow']['level'] = 'DEBUG'
    elif args.verbose:
        settings.LOGGING['loggers']['htsworkflow']['level'] = 'INFO'

    django.setup()

    model = get_model(args.model, args.db_path)
    submission_names = list(list_submissions(model))
    name = args.name
    if len(submission_names) == 0 and args.name is None:
        parser.error("Please name this submission")
    elif args.name and submission_names and args.name not in submission_names:
        parser.error("{} is not in this model. Choose from: {}{}".format(
            args.name,
            os.linesep,
            INDENTED.join(submission_names)))
    elif args.name is None and len(submission_names) > 1:
        parser.error("Please choose submission name from: {}{}".format(
            os.linesep,
            INDENTED.join(submission_names)))
    elif len(submission_names) == 1:
        name = submission_names[0]

    if name:
        submission_uri = get_submission_uri(name)
        logger.info('Submission URI: %s', submission_uri)

    mapper = AWSSubmission(name, model, encode_host=args.encoded, lims_host=args.host)

    if args.load_rdf is not None:
        if submission_uri is None:
            parser.error("Please specify the submission name")
        load_into_model(model, 'turtle', args.load_rdf, submission_uri)

    results = ResultMap()
    for a in args.libraries:
        if os.path.exists(a):
            results.add_results_from_file(a)
        else:
            logger.warn("File %s doesn't exist.", a)

    if args.make_link_tree_from is not None:
        results.make_tree_from(args.make_link_tree_from, link=True)

    if args.copy_tree_from is not None:
        results.make_tree_from(args.copy_tree_from, link=False)

    if args.fastq:
        logger.info("Building fastq extraction scripts")
        flowcells = os.path.join(args.sequence, 'flowcells')
        extractor = CondorFastqExtract(args.host, flowcells,
                                       model=args.model,
                                       compression=args.compression,
                                       force=args.force)
        extractor.create_scripts(results)

    if args.scan_submission:
        if name is None:
            parser.error("Please define a submission name")
        mapper.scan_submission_dirs(results)

    if args.upload:
        mapper.upload(results, args.dry_run)

    if args.check_upload:
        mapper.check_upload(results)

    if args.sparql:
        sparql_query(model, args.sparql)

    if args.print_rdf:
        writer = get_serializer()
        print(writer.serialize_model_to_string(model))


def make_parser():
    parser = argparse.ArgumentParser()

    model = parser.add_argument_group('model')
    model.add_argument('--name', help="Set submission name")
    model.add_argument('--db-path', default=None,
                     help="set rdf database path")
    model.add_argument('--model', default=None,
                     help="Load model database")
    model.add_argument('--load-rdf', default=None,
                     help="load rdf statements into model")
    model.add_argument('--sparql', default=None, help="execute sparql query")
    model.add_argument('--print-rdf', action="store_true", default=False,
                     help="print ending model state")

    # commands
    commands = parser.add_argument_group('commands')
    commands.add_argument('--make-link-tree-from',
                        help="create directories & link data files",
                        default=None)
    commands.add_argument('--copy-tree-from',
                        help="create directories & copy data files",
                        default=None)
    commands.add_argument('--fastq', default=False, action="store_true",
                        help="generate scripts for making fastq files")
    commands.add_argument('--scan-submission', default=False, action="store_true",
                        help="cache md5 sums")
    commands.add_argument('--upload', default=False, action="store_true",
                        help="Upload files")
    commands.add_argument('--check-upload', default=False, action='store_true',
                          help='check to see files are actually uploaded')

    parser.add_argument('--force', default=False, action="store_true",
                      help="Force regenerating fastqs")
    parser.add_argument('--compression', default=None,
                      choices=['gzip'],
                      help='select compression type for fastq files')
    parser.add_argument('--library-url', default=None,
                      help="specify an alternate source for library information")
    parser.add_argument('--encoded', default='www.encodeproject.org',
                      help='base url for talking to encode server')
    parser.add_argument('--dry-run', default=False, action='store_true',
                      help='avoid making changes to encoded')
    
    # debugging
    parser.add_argument('--verbose', default=False, action="store_true",
                      help='verbose logging')
    parser.add_argument('--debug', default=False, action="store_true",
                      help='debug logging')

    api.add_auth_options(parser)
     
    parser.add_argument('libraries', nargs='+',
                        help='mapping of library id to directory to be processed')

    return parser

if __name__ == "__main__":
    main()
