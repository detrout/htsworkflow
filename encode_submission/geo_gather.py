#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import logging
from optparse import OptionParser, OptionGroup
import os


if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'htsworkflow.settings'


from htsworkflow.util import api
from htsworkflow.util.rdfhelp import \
     get_model, \
     get_serializer, \
     load_into_model, \
     sparql_query
from htsworkflow.submission.daf import get_submission_uri
from htsworkflow.submission.results import ResultMap
from htsworkflow.submission.geo import GEOSubmission
from htsworkflow.submission.condorfastq import CondorFastqExtract

logger = logging.getLogger(__name__)


def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    submission_uri = None

    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif opts.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    model = get_model(opts.model, opts.db_path)
    mapper = None
    if opts.name:
        mapper = GEOSubmission(opts.name,  model, host=opts.host)
        submission_uri = get_submission_uri(opts.name)

    if opts.load_rdf is not None:
        if submission_uri is None:
            parser.error("Please specify the submission name")
        load_into_model(model, 'turtle', opts.load_rdf, submission_uri)

    results = ResultMap()
    for a in args:
        if os.path.exists(a):
            results.add_results_from_file(a)
        else:
            logger.warning("File %s doesn't exist.", a)

    if opts.make_tree_from is not None:
        results.make_tree_from(opts.make_tree_from)

    if opts.fastq:
        logger.info("Building fastq extraction scripts")
        flowcells = os.path.join(opts.sequence, 'flowcells')
        extractor = CondorFastqExtract(opts.host, flowcells,
                                       model=opts.model,
                                       force=opts.force)
        extractor.create_scripts(results)

    if opts.scan_submission:
        if opts.name is None:
            parser.error("Please define a submission name")
        mapper.scan_submission_dirs(results)

    if opts.make_soft:
        mapper.make_soft(results)

    if opts.sparql:
        sparql_query(model, opts.sparql)

    if opts.print_rdf:
        writer = get_serializer()
        print(writer.serialize_model_to_string(model))


def make_parser():
    parser = OptionParser()

    model = OptionGroup(parser, 'model')
    model.add_option('--name', help="Set submission name")
    model.add_option('--db-path', default=None,
                     help="set rdf database path")
    model.add_option('--model', default=None,
                     help="Load model database")
    model.add_option('--load-rdf', default=None,
                     help="load rdf statements into model")
    model.add_option('--sparql', default=None, help="execute sparql query")
    model.add_option('--print-rdf', action="store_true", default=False,
                     help="print ending model state")
    parser.add_option_group(model)
    # commands
    commands = OptionGroup(parser, 'commands')
    commands.add_option('--make-tree-from',
                        help="create directories & link data files",
                        default=None)
    commands.add_option('--fastq', default=False, action="store_true",
                        help="generate scripts for making fastq files")
    commands.add_option('--scan-submission', default=False, action="store_true",
                        help="Import metadata for submission into our model")
    commands.add_option('--make-soft', help='make the soft file', default=False,
                        action="store_true")

    parser.add_option_group(commands)

    parser.add_option('--force', default=False, action="store_true",
                      help="Force regenerating fastqs")
    parser.add_option('--daf', default=None, help='specify daf name')
    parser.add_option('--library-url', default=None,
                      help="specify an alternate source for library information")
    # debugging
    parser.add_option('--verbose', default=False, action="store_true",
                      help='verbose logging')
    parser.add_option('--debug', default=False, action="store_true",
                      help='debug logging')

    api.add_auth_options(parser)

    return parser


if __name__ == "__main__":
    main()
