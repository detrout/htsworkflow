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
from htsworkflow.submission.daf import \
     DAFMapper, \
     MetadataLookupException, \
     get_submission_uri
from htsworkflow.submission.condorfastq import CondorFastqExtract

logger = logging.getLogger('ucsc_gather')

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    submission_uri = None

    if opts.debug:
        logging.basicConfig(level = logging.DEBUG )
    elif opts.verbose:
        logging.basicConfig(level = logging.INFO )
    else:
        logging.basicConfig(level = logging.WARNING )

    apidata = api.make_auth_from_opts(opts, parser)

    model = get_model(opts.model, opts.db_path)
    if opts.name:
        mapper = DAFMapper(opts.name, opts.daf,  model)
        if opts.library_url is not None:
            mapper.library_url = opts.library_url
        submission_uri = get_submission_uri(opts.name)


    if opts.load_rdf is not None:
        if submission_uri is None:
            parser.error("Please specify the submission name")
        load_into_model(model, 'turtle', opts.load_rdf, submission_uri)

    if opts.make_ddf and opts.daf is None:
        parser.error("Please specify your daf when making ddf files")

    library_result_map = []
    for a in args:
        library_result_map.extend(read_library_result_map(a))

    if opts.make_tree_from is not None:
        make_tree_from(opts.make_tree_from, library_result_map)

    if opts.link_daf:
        if opts.daf is None:
            parser.error("Please specify daf filename with --daf")
        link_daf(opts.daf, library_result_map)

    if opts.fastq:
        extractor = CondorFastqExtract(opts.host, apidata, opts.sequence,
                                       force=opts.force)
        extractor.build_fastqs(library_result_map)

    if opts.scan_submission:
        scan_submission_dirs(mapper, library_result_map)

    if opts.make_ddf:
        make_all_ddfs(mapper, library_result_map, opts.daf, force=opts.force)

    if opts.sparql:
        sparql_query(model, opts.sparql)

    if opts.print_rdf:
        writer = get_serializer()
        print writer.serialize_model_to_string(model)


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
    commands.add_option('--link-daf', default=False, action="store_true",
                        help="link daf into submission directories")
    commands.add_option('--make-ddf', help='make the ddfs', default=False,
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

def make_tree_from(source_path, library_result_map):
    """Create a tree using data files from source path.
    """
    for lib_id, lib_path in library_result_map:
        if not os.path.exists(lib_path):
            logger.info("Making dir {0}".format(lib_path))
            os.mkdir(lib_path)
        source_lib_dir = os.path.abspath(os.path.join(source_path, lib_path))
        if os.path.exists(source_lib_dir):
            pass
        for filename in os.listdir(source_lib_dir):
            source_pathname = os.path.join(source_lib_dir, filename)
            target_pathname = os.path.join(lib_path, filename)
            if not os.path.exists(source_pathname):
                raise IOError("{0} does not exist".format(source_pathname))
            if not os.path.exists(target_pathname):
                os.symlink(source_pathname, target_pathname)
                logger.info(
                    'LINK {0} to {1}'.format(source_pathname, target_pathname))


def link_daf(daf_path, library_result_map):
    if not os.path.exists(daf_path):
        raise RuntimeError("%s does not exist, how can I link to it?" % (daf_path,))

    base_daf = os.path.basename(daf_path)

    for lib_id, result_dir in library_result_map:
        if not os.path.exists(result_dir):
            raise RuntimeError("Couldn't find target directory %s" %(result_dir,))
        submission_daf = os.path.join(result_dir, base_daf)
        if not os.path.exists(submission_daf):
            if not os.path.exists(daf_path):
                raise RuntimeError("Couldn't find daf: %s" %(daf_path,))
            os.link(daf_path, submission_daf)


def scan_submission_dirs(view_map, library_result_map):
    """Look through our submission directories and collect needed information
    """
    for lib_id, result_dir in library_result_map:
        logger.info("Importing %s from %s" % (lib_id, result_dir))
        try:
            view_map.import_submission_dir(result_dir, lib_id)
        except MetadataLookupException, e:
            logger.error("Skipping %s: %s" % (lib_id, str(e)))

def make_all_ddfs(view_map, library_result_map, daf_name, make_condor=True, force=False):
    dag_fragment = []
    for lib_id, result_dir in library_result_map:
        submissionNode = view_map.get_submission_node(result_dir)
        dag_fragment.extend(
            make_ddf(view_map, submissionNode, daf_name, make_condor, result_dir)
        )

    if make_condor and len(dag_fragment) > 0:
        dag_filename = 'submission.dagman'
        if not force and os.path.exists(dag_filename):
            logger.warn("%s exists, please delete" % (dag_filename,))
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
  OPTIONAL { ?library libraryOntology:condition ?treatment }
  OPTIONAL { ?library ucscDaf:protocol ?protocol }
  OPTIONAL { ?library ucscDaf:readType ?readType }
  OPTIONAL { ?library ucscDaf:strain ?strain }
  OPTIONAL { ?library libraryOntology:insert_size ?insertLength }
  OPTIONAL { ?library ucscDaf:mapAlgorithm ?mapAlgorithm }
}
ORDER BY  ?submitView"""
    dag_fragments = []

    name = fromTypedNode(view_map.model.get_target(submissionNode, submissionOntology['name']))
    if name is None:
        logger.error("Need name for %s" % (str(submissionNode)))
        return []

    ddf_name = name + '.ddf'
    if outdir is not None:
        outfile = os.path.join(outdir, ddf_name)
        output = open(outfile,'w')
    else:
        outfile = 'stdout:'
        output = sys.stdout

    formatted_query = query_template % {'submission': str(submissionNode.uri)}

    query = RDF.SPARQLQuery(formatted_query)
    results = query.execute(view_map.model)

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
                logger.warn("{0}: {1} was None".format(outfile, variable_name))
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


def read_library_result_map(filename):
    """
    Read a file that maps library id to result directory.
    Does not support spaces in filenames.

    For example:
      10000 result/foo/bar
    """
    stream = open(filename,'r')

    results = []
    for line in stream:
        line = line.rstrip()
        if not line.startswith('#') and len(line) > 0 :
            library_id, result_dir = line.split()
            results.append((library_id, result_dir))
    return results


def make_condor_archive_script(name, files, outdir=None):
    script = """Universe = vanilla

Executable = /bin/tar
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
               'user': os.getlogin()}

    condor_script = os.path.join(outdir, make_condor_name(name, 'archive'))
    condor_stream = open(condor_script,'w')
    condor_stream.write(script % context)
    condor_stream.close()
    return condor_script


def make_condor_upload_script(name, outdir=None):
    script = """Universe = vanilla

Executable = /usr/bin/lftp
arguments = -c put ../%(archivename)s -o ftp://%(ftpuser)s:%(ftppassword)s@%(ftphost)s/%(archivename)s

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
               'ftphost': encodeftp}

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


def get_library_info(host, apidata, library_id):
    url = api.library_url(host, library_id)
    contents = api.retrieve_info(url, apidata)
    return contents


def make_submission_section(line_counter, files, attributes):
    """
    Create a section in the submission ini file
    """
    inifile = [ "[line%s]" % (line_counter,) ]
    inifile += ["files=%s" % (",".join(files))]

    for k,v in attributes.items():
        inifile += ["%s=%s" % (k,v)]
    return inifile


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
