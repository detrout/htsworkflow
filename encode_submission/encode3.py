"""Create a track hub
"""

#!/usr/bin/env python
from ConfigParser import SafeConfigParser
import fnmatch
from glob import glob
import json
import logging
import netrc
from optparse import OptionParser, OptionGroup
import os
from pprint import pprint, pformat
import shlex
from StringIO import StringIO
import stat
import sys
import time
import types
import urllib
import urllib2
import urlparse
from zipfile import ZipFile

import RDF

from htsworkflow.util import api
from htsworkflow.util.rdfhelp import \
    dafTermOntology, \
    fromTypedNode, \
    get_model, \
    get_serializer, \
    load_into_model, \
    sparql_query, \
    submissionOntology
from htsworkflow.submission.daf import get_submission_uri
from htsworkflow.submission.submission import list_submissions
from htsworkflow.submission.results import ResultMap
from htsworkflow.submission.trackhub_submission import TrackHubSubmission
from htsworkflow.submission.condorfastq import CondorFastqExtract

logger = logging.getLogger(__name__)

INDENTED = "  " + os.linesep

import django
if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'htsworkflow.settings.local'

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    submission_uri = None

    from django.conf import settings

    if opts.debug:
        settings.LOGGING['loggers']['level'] = 'DEBUG'
    elif opts.verbose:
        settings.LOGGING['loggers']['level'] = 'INFO'

    model = get_model(opts.model, opts.db_path)

    submission_names = list(list_submissions(model))
    name = opts.name
    if len(submission_names) == 0 and opts.name is None:
        parser.error("Please name this submission")
    elif opts.name and submission_names and opts.name not in submission_names:
        parser.error("{} is not in this model. Choose from: {}{}".format(
            opts.name,
            os.linesep,
            INDENTED.join(submission_names)))
    elif opts.name is None and len(submission_names) > 1:
        parser.error("Please choose submission name from: {}{}".format(
            os.linesep,
            INDENTED.join(submission_names)))
    elif len(submission_names) == 1:
        name = submission_names[0]

    if name:
        submission_uri = get_submission_uri(name)
        logger.info('Submission URI: %s', name)
    else:
        logger.debug('No name, unable to create submission ur')

    mapper = None
    if opts.make_track_hub:
        mapper = TrackHubSubmission(name,
                                    model,
                                    baseurl=opts.make_track_hub,
                                    baseupload=opts.track_hub_upload,
                                    host=opts.host)

    if opts.load_rdf is not None:
        if submission_uri is None:
            parser.error("Please specify the submission name")
        load_into_model(model, 'turtle', opts.load_rdf, submission_uri)

    results = ResultMap()
    for a in args:
        if os.path.exists(a):
            results.add_results_from_file(a)
        else:
            logger.warn("File %s doesn't exist.", a)

    if opts.make_link_tree_from is not None:
        results.make_tree_from(opts.make_link_tree_from, link=True)

    if opts.copy_tree_from is not None:
        results.make_tree_from(opts.copy_tree_from, link=False)

    if opts.fastq:
        logger.info("Building fastq extraction scripts")
        flowcells = os.path.join(opts.sequence, 'flowcells')
        extractor = CondorFastqExtract(opts.host, flowcells,
                                       model=opts.model,
                                       compression=opts.compression,
                                       force=opts.force)
        extractor.create_scripts(results)

    if opts.scan_submission:
        if name is None:
            parser.error("Please define a submission name")
        if mapper is None:
            parser.error("Scan submission needs --make-track-hub=public-url")
        mapper.scan_submission_dirs(results)

    if opts.make_track_hub:
        trackdb = mapper.make_hub(results)

    if opts.make_manifest:
        make_manifest(mapper, results, opts.make_manifest)

    if opts.sparql:
        sparql_query(model, opts.sparql)

    if opts.print_rdf:
        writer = get_serializer()
        print writer.serialize_model_to_string(model)


def make_manifest(mapper, results, filename=None):
    manifest = mapper.make_manifest(results)

    if filename is None or filename == '-':
        sys.stdout.write(manifest)
    else:
        with open(filename, 'w') as mainifeststream:
            mainifeststream.write(manifest)


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
    commands.add_option('--make-link-tree-from',
                        help="create directories & link data files",
                        default=None)
    commands.add_option('--copy-tree-from',
                        help="create directories & copy data files",
                        default=None)
    commands.add_option('--fastq', default=False, action="store_true",
                        help="generate scripts for making fastq files")
    commands.add_option('--scan-submission', default=False, action="store_true",
                        help="Import metadata for submission into our model")
    commands.add_option('--make-track-hub', default=None,
                        help='web root that will host the trackhub.')
    commands.add_option('--track-hub-upload', default=None,
                        help='where to upload track hub <host>:<path>')
    commands.add_option('--make-manifest',
                        help='name the manifest file name or - for stdout to create it',
                        default=None)

    parser.add_option_group(commands)

    parser.add_option('--force', default=False, action="store_true",
                      help="Force regenerating fastqs")
    parser.add_option('--compression', default=None, type='choice',
                      choices=['gzip'],
                      help='select compression type for fastq files')
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
    django.setup()

    main()
