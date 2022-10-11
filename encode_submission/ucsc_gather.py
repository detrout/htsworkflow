#!/usr/bin/env python
from __future__ import print_function, unicode_literals

from six.moves.configparser import SafeConfigParser
import fnmatch
from glob import glob
import json
import logging
import netrc
from optparse import OptionParser, OptionGroup
import os
from pprint import pprint, pformat
import shlex
from six.moves import StringIO
import stat
import sys
import time
import types
from zipfile import ZipFile

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'htsworkflow.settings'

from htsworkflow.util import api
from encoded_client.rdfns import \
     dafTermOntology, \
     submissionOntology
from htsworkflow.submission.daf import \
     UCSCSubmission, \
     MetadataLookupException, \
     get_submission_uri
from htsworkflow.submission.results import ResultMap
from htsworkflow.submission.condorfastq import CondorFastqExtract

logger = logging.getLogger('ucsc_gather')

TAR = '/bin/tar'
LFTP = '/usr/bin/lftp'

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    submission_uri = None

    global TAR
    global LFTP
    TAR = opts.tar
    LFTP = opts.lftp

    if opts.debug:
        logging.basicConfig(level = logging.DEBUG )
    elif opts.verbose:
        logging.basicConfig(level = logging.INFO )
    else:
        logging.basicConfig(level = logging.WARNING )

    apidata = api.make_auth_from_opts(opts, parser)

    model = get_model(opts.model, opts.db_path)
    mapper = None
    if opts.name:
        mapper = UCSCSubmission(opts.name, opts.daf,  model)
        if opts.library_url is not None:
            mapper.library_url = opts.library_url
        submission_uri = get_submission_uri(opts.name)


    if opts.load_rdf is not None:
        if submission_uri is None:
            parser.error("Please specify the submission name")
        load_into_model(model, 'turtle', opts.load_rdf, submission_uri)

    if opts.make_ddf and opts.daf is None:
        parser.error("Please specify your daf when making ddf files")

    results = ResultMap()
    for a in args:
        results.add_results_from_file(a)

    if opts.make_tree_from is not None:
        results.make_tree_from(opts.make_tree_from)

    if opts.link_daf:
        if mapper is None:
            parser.error("Specify a submission model")
        if mapper.daf is None:
            parser.error("Please load a daf first")
        mapper.link_daf(results)

    if opts.fastq:
        flowcells = os.path.join(opts.sequence, 'flowcells')
        extractor = CondorFastqExtract(opts.host, flowcells,
                                       force=opts.force)
        extractor.create_scripts(results)

    if opts.scan_submission:
        mapper.scan_submission_dirs(results)

    if opts.make_ddf:
        if not os.path.exists(TAR):
            parser.error("%s does not exist, please specify --tar" % (TAR,))
        if not os.path.exists(LFTP):
            parser.error("%s does not exist, please specify --lftp" % (LFTP,))
        make_all_ddfs(mapper, results, opts.daf, force=opts.force)

    if opts.zip_ddf:
        zip_ddfs(mapper, results, opts.daf)

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
    model.add_option('--tar', default=TAR,
                     help="override path to tar command")
    model.add_option('--lftp', default=LFTP,
                     help="override path to lftp command")
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
    commands.add_option('--link-daf', default=False, action="store_true",
                        help="link daf into submission directories")
    commands.add_option('--make-ddf', help='make the ddfs', default=False,
                      action="store_true")
    commands.add_option('--zip-ddf', default=False, action='store_true',
                        help='zip up just the metadata')

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


def make_all_ddfs(view_map, library_result_map, daf_name, make_condor=True, force=False):
    dag_fragment = []
    for lib_id, result_dir in library_result_map.items():
        submissionNode = view_map.get_submission_node(result_dir)
        dag_fragment.extend(
            make_ddf(view_map, submissionNode, daf_name, make_condor, result_dir)
        )

    if make_condor and len(dag_fragment) > 0:
        dag_filename = 'submission.dagman'
        if not force and os.path.exists(dag_filename):
            logger.warning("%s exists, please delete" % (dag_filename,))
        else:
            f = open(dag_filename,'w')
            f.write( os.linesep.join(dag_fragment))
            f.write( os.linesep )
            f.close()


def make_ddf(view_map, submissionNode, daf_name, make_condor=False, outdir=None):
    """
    Make ddf files, and bonus condor file
    """
    query_template = """PREFIX libraryOntology: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>
PREFIX submissionOntology: <http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#>
PREFIX ucscDaf: <http://jumpgate.caltech.edu/wiki/UcscDaf#>

select ?submitView  ?files ?md5sum ?view ?cell ?antibody ?sex ?control ?strain ?controlId ?labExpId ?labVersion ?treatment ?protocol ?readType ?insertLength ?replicate ?mapAlgorithm
WHERE {
  ?file ucscDaf:filename ?files ;
        ucscDaf:md5sum ?md5sum .
  ?submitView ucscDaf:has_file ?file ;
              ucscDaf:view ?dafView ;
              ucscDaf:submission <%(submission)s> .
  ?dafView ucscDaf:name ?view .
  <%(submission)s> submissionOntology:library ?library ;

  OPTIONAL { ?library libraryOntology:antibody ?antibody }
  OPTIONAL { ?library libraryOntology:cell_line ?cell }
  OPTIONAL { <%(submission)s> ucscDaf:control ?control }
  OPTIONAL { <%(submission)s> ucscDaf:controlId ?controlId }
  OPTIONAL { ?library ucscDaf:sex ?sex }
  OPTIONAL { ?library libraryOntology:library_id ?labExpId }
  OPTIONAL { ?library libraryOntology:library_id ?labVersion }
  OPTIONAL { ?library libraryOntology:replicate ?replicate }
  OPTIONAL { ?library libraryOntology:condition_term ?treatment }
  OPTIONAL { ?library ucscDaf:protocol ?protocol }
  OPTIONAL { ?library ucscDaf:readType ?readType }
  OPTIONAL { ?library ucscDaf:strain ?strain }
  OPTIONAL { ?library libraryOntology:insert_size ?insertLength }
  OPTIONAL { ?library ucscDaf:mapAlgorithm ?mapAlgorithm }
}
ORDER BY  ?submitView"""
    dag_fragments = []

    names = list(view_map.model.objects(submissionNode, submissionOntology['name']))
    if len(names) == 0:
        logger.error("Need name for %s" % (str(submissionNode)))
        return []

    ddf_name = make_ddf_name(names[0].toPython())
    if outdir is not None:
        outfile = os.path.join(outdir, ddf_name)
        output = open(outfile,'w')
    else:
        outfile = 'stdout:'
        output = sys.stdout

    formatted_query = query_template % {'submission': str(submissionNode.uri)}

    results = view_map.model.query(formatted_query)

    # filename goes first
    variables = view_map.get_daf_variables()
    # 'controlId',
    output.write('\t'.join(variables))
    output.write(os.linesep)

    all_views = {}
    all_files = []
    for row in results:
        viewname = fromTypedNode(row['view'])
        current = all_views.setdefault(viewname, {})
        for variable_name in variables:
            value = str(fromTypedNode(row[variable_name]))
            if value is None or value == 'None':
                logger.warning("{0}: {1} was None".format(outfile, variable_name))
            if variable_name in ('files', 'md5sum'):
                current.setdefault(variable_name,[]).append(value)
            else:
                current[variable_name] = value

    for view in all_views.keys():
        line = []
        for variable_name in variables:
            if variable_name in ('files', 'md5sum'):
                line.append(','.join(all_views[view][variable_name]))
            else:
                line.append(all_views[view][variable_name])
        output.write("\t".join(line))
        output.write(os.linesep)
        all_files.extend(all_views[view]['files'])

    logger.info(
        "Examined {0}, found files: {1}".format(
            str(submissionNode), ", ".join(all_files)))

    all_files.append(daf_name)
    all_files.append(ddf_name)

    if make_condor:
        archive_condor = make_condor_archive_script(name, all_files, outdir)
        upload_condor = make_condor_upload_script(name, outdir)

        dag_fragments.extend(
            make_dag_fragment(name, archive_condor, upload_condor)
        )

    return dag_fragments


def zip_ddfs(view_map, library_result_map, daf_name):
    """zip up just the ddf & daf files
    """
    rootdir = os.getcwd()
    for lib_id, result_dir in library_result_map:
        submissionNode = view_map.get_submission_node(result_dir)
        nameNodes = list(view_map.model.objects(submissionNode,
                                                submissionOntology['name']))
        if len(nameNodes) == 0:
            logger.error("Need name for %s" % (str(submissionNode)))
            continue
        name = nameNodes[0].toPython()

        zip_name = '../{0}.zip'.format(lib_id)
        os.chdir(os.path.join(rootdir, result_dir))
        with ZipFile(zip_name, 'w') as stream:
            stream.write(make_ddf_name(name))
            stream.write(daf_name)
        os.chdir(rootdir)


def make_condor_archive_script(name, files, outdir=None):
    script = """Universe = vanilla

Executable = %(tar)s
arguments = czvhf ../%(archivename)s %(filelist)s

Error = compress.out.$(Process).log
Output = compress.out.$(Process).log
Log = /tmp/submission-compress-%(user)s.log
initialdir = %(initialdir)s
environment="GZIP=-3"
request_memory = 20

queue
"""
    if outdir is None:
        outdir = os.getcwd()
    for f in files:
        pathname = os.path.join(outdir, f)
        if not os.path.exists(pathname):
            raise RuntimeError("Missing %s from %s" % (f,outdir))

    context = {'archivename': make_submission_name(name),
               'filelist': " ".join(files),
               'initialdir': os.path.abspath(outdir),
               'user': os.getlogin(),
               'tar': TAR}

    condor_script = os.path.join(outdir, make_condor_name(name, 'archive'))
    condor_stream = open(condor_script,'w')
    condor_stream.write(script % context)
    condor_stream.close()
    return condor_script


def make_condor_upload_script(name, lftp, outdir=None):
    script = """Universe = vanilla

Executable = %(lftp)s
arguments = -c put %(archivename)s -o ftp://%(ftpuser)s:%(ftppassword)s@%(ftphost)s/%(archivename)s

Error = upload.out.$(Process).log
Output = upload.out.$(Process).log
Log = /tmp/submission-upload-%(user)s.log
initialdir = %(initialdir)s

queue
"""
    if outdir is None:
        outdir = os.getcwd()

    auth = netrc.netrc(os.path.expanduser("~diane/.netrc"))

    encodeftp = 'encodeftp.cse.ucsc.edu'
    ftpuser = auth.hosts[encodeftp][0]
    ftppassword = auth.hosts[encodeftp][2]
    context = {'archivename': make_submission_name(name),
               'initialdir': os.path.abspath(outdir),
               'user': os.getlogin(),
               'ftpuser': ftpuser,
               'ftppassword': ftppassword,
               'ftphost': encodeftp,
               'lftp': LFTP}

    condor_script = os.path.join(outdir, make_condor_name(name, 'upload'))
    condor_stream = open(condor_script,'w')
    condor_stream.write(script % context)
    condor_stream.close()
    os.chmod(condor_script, stat.S_IREAD|stat.S_IWRITE)

    return condor_script


def make_dag_fragment(ininame, archive_condor, upload_condor):
    """
    Make the couple of fragments compress and then upload the data.
    """
    cur_dir = os.getcwd()
    archive_condor = os.path.join(cur_dir, archive_condor)
    upload_condor = os.path.join(cur_dir, upload_condor)
    job_basename = make_base_name(ininame)

    fragments = []
    fragments.append('JOB %s_archive %s' % (job_basename, archive_condor))
    fragments.append('JOB %s_upload %s' % (job_basename,  upload_condor))
    fragments.append('PARENT %s_archive CHILD %s_upload' % (job_basename, job_basename))

    return fragments


def make_base_name(pathname):
    base = os.path.basename(pathname)
    name, ext = os.path.splitext(base)
    return name


def make_submission_name(ininame):
    name = make_base_name(ininame)
    return name + ".tgz"


def make_ddf_name(pathname):
    name = make_base_name(pathname)
    return name + ".ddf"


def make_condor_name(pathname, run_type=None):
    name = make_base_name(pathname)
    elements = [name]
    if run_type is not None:
        elements.append(run_type)
    elements.append("condor")
    return ".".join(elements)


def parse_filelist(file_string):
    return file_string.split(",")


def validate_filelist(files):
    """
    Die if a file doesn't exist in a file list
    """
    for f in files:
        if not os.path.exists(f):
            raise RuntimeError("%s does not exist" % (f,))

if __name__ == "__main__":
    main()
