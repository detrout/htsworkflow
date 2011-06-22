#!/usr/bin/env python
from ConfigParser import SafeConfigParser
import fnmatch
from glob import glob
import json
import logging
import netrc
from optparse import OptionParser
import os
from pprint import pprint, pformat
import shlex
from StringIO import StringIO
import stat
from subprocess import Popen, PIPE
import sys
import time
import types
import urllib
import urllib2
import urlparse

from htsworkflow.util import api
from htsworkflow.util.rdfhelp import \
     dafTermOntology, \
     fromTypedNode, \
     get_model, \
     get_serializer, \
     load_into_model, \
     submissionOntology 
from htsworkflow.submission.daf import DAFMapper, get_submission_uri
from htsworkflow.submission.condorfastq import CondorFastqExtract

logger = logging.getLogger('ucsc_gather')

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    
    if opts.debug:
        logging.basicConfig(level = logging.DEBUG )
    elif opts.verbose:
        logging.basicConfig(level = logging.INFO )
    else:
        logging.basicConfig(level = logging.WARNING )        
    
    apidata = api.make_auth_from_opts(opts, parser)

    model = get_model(opts.load_model)
    if opts.name:
        mapper = DAFMapper(opts.name, opts.daf,  model)
        submission_uri = get_submission_uri(opts.name)
        
    if opts.load_rdf is not None:
        load_into_model(model, 'turtle', opts.load_rdf, submission_uri)

    if opts.makeddf and opts.daf is None:
        parser.error("Please specify your daf when making ddf files")

    if len(args) == 0:
        parser.error("I need at least one library submission-dir input file")
        
    library_result_map = []
    for a in args:
        library_result_map.extend(read_library_result_map(a))

    if opts.make_tree_from is not None:
        make_tree_from(opts.make_tree_from, library_result_map)
            
    #if opts.daf is not None:
    #    link_daf(opts.daf, library_result_map)

    if opts.fastq:
        extractor = CondorFastqExtract(opts.host, apidata, opts.sequence,
                                       force=opts.force)
        extractor.build_fastqs(library_result_map)

    if opts.scan_submission:
        scan_submission_dirs(mapper, library_result_map)

    if opts.makeddf:
        make_all_ddfs(mapper, library_result_map, force=opts.force)

    if opts.print_rdf:
        writer = get_serializer()
        print writer.serialize_model_to_string(model)

        
def make_parser():
    parser = OptionParser()

    parser.add_option('--name', help="Set submission name")
    parser.add_option('--load-model', default=None,
      help="Load model database")
    parser.add_option('--load-rdf', default=None,
      help="load rdf statements into model")
    parser.add_option('--print-rdf', action="store_true", default=False,
      help="print ending model state")

    # commands
    parser.add_option('--make-tree-from',
                      help="create directories & link data files",
                      default=None)
    parser.add_option('--fastq', help="generate scripts for making fastq files",
                      default=False, action="store_true")

    parser.add_option('--scan-submission', default=False, action="store_true",
                      help="Import metadata for submission into our model")
    
    parser.add_option('--makeddf', help='make the ddfs', default=False,
                      action="store_true")
    
    parser.add_option('--daf', default=None, help='specify daf name')
    parser.add_option('--force', default=False, action="store_true",
                      help="Force regenerating fastqs")

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
            logging.info("Making dir {0}".format(lib_path))
            os.mkdir(lib_path)
        source_lib_dir = os.path.join(source_path, lib_path)
        if os.path.exists(source_lib_dir):
            pass
        for filename in os.listdir(source_lib_dir):
            source_pathname = os.path.join(source_lib_dir, filename)
            target_pathname = os.path.join(lib_path, filename)
            if not os.path.exists(source_pathname):
                raise IOError("{0} does not exist".format(source_pathname))
            if not os.path.exists(target_pathname):
                os.symlink(source_pathname, target_pathname)
                logging.info(
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
        view_map.import_submission_dir(result_dir, lib_id)
        
def make_all_ddfs(view_map, library_result_map, make_condor=True, force=False):
    dag_fragment = []
    for lib_id, result_dir in library_result_map:
        submissionNode = view_map.get_submission_node(result_dir)
        dag_fragment.extend(
            make_ddf(view_map, submissionNode, make_condor, result_dir)
        )

    if make_condor and len(dag_fragment) > 0:
        dag_filename = 'submission.dagman'
        if not force and os.path.exists(dag_filename):
            logging.warn("%s exists, please delete" % (dag_filename,))
        else:
            f = open(dag_filename,'w')
            f.write( os.linesep.join(dag_fragment))
            f.write( os.linesep )
            f.close()
            

def make_ddf(view_map, submissionNode, make_condor=False, outdir=None):
    """
    Make ddf files, and bonus condor file
    """
    dag_fragments = []
    curdir = os.getcwd()
    if outdir is not None:
        os.chdir(outdir)
    output = sys.stdout

    name = fromTypedNode(view_map.model.get_target(submissionNode, submissionOntology['name']))
    if name is None:
        logging.error("Need name for %s" % (str(submissionNode)))
        return []
    
    ddf_name = name + '.ddf'
    output = sys.stdout
    # output = open(ddf_name,'w')

    # filename goes first
    variables = ['filename']
    variables.extend(view_map.get_daf_variables())
    output.write('\t'.join(variables))
    output.write(os.linesep)
    
    submission_views = view_map.model.get_targets(submissionNode, submissionOntology['has_view'])
    file_list = []
    for viewNode in submission_views:
        record = []
        for variable_name in variables:
            varNode = dafTermOntology[variable_name]
            values = [fromTypedNode(v) for v in list(view_map.model.get_targets(viewNode, varNode))]
            if variable_name == 'filename':
                file_list.extend(values)
            if len(values) == 0:
                attribute = "#None#"
            elif len(values) == 1:
                attribute = values[0]
            else:
                attribute = ",".join(values)
            record.append(attribute)
        output.write('\t'.join(record))
        output.write(os.linesep)
            
    logging.info(
        "Examined {0}, found files: {1}".format(
            str(submissionNode), ", ".join(file_list)))

    #file_list.append(daf_name)
    #if ddf_name is not None:
    #    file_list.append(ddf_name)
    #
    #if make_condor:
    #    archive_condor = make_condor_archive_script(ininame, file_list)
    #    upload_condor = make_condor_upload_script(ininame)
    #    
    #    dag_fragments.extend( 
    #        make_dag_fragment(ininame, archive_condor, upload_condor)
    #    ) 
        
    os.chdir(curdir)
    
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


def make_condor_archive_script(ininame, files):
    script = """Universe = vanilla

Executable = /bin/tar
arguments = czvhf ../%(archivename)s %(filelist)s

Error = compress.err.$(Process).log
Output = compress.out.$(Process).log
Log = /tmp/submission-compress-%(user)s.log
initialdir = %(initialdir)s
environment="GZIP=-3"
request_memory = 20

queue 
"""
    for f in files:
        if not os.path.exists(f):
            raise RuntimeError("Missing %s" % (f,))

    context = {'archivename': make_submission_name(ininame),
               'filelist': " ".join(files),
               'initialdir': os.getcwd(),
               'user': os.getlogin()}

    condor_script = make_condor_name(ininame, 'archive')
    condor_stream = open(condor_script,'w')
    condor_stream.write(script % context)
    condor_stream.close()
    return condor_script


def make_condor_upload_script(ininame):
    script = """Universe = vanilla

Executable = /usr/bin/lftp
arguments = -c put ../%(archivename)s -o ftp://%(ftpuser)s:%(ftppassword)s@%(ftphost)s/%(archivename)s

Error = upload.err.$(Process).log
Output = upload.out.$(Process).log
Log = /tmp/submission-upload-%(user)s.log
initialdir = %(initialdir)s

queue 
"""
    auth = netrc.netrc(os.path.expanduser("~diane/.netrc"))
    
    encodeftp = 'encodeftp.cse.ucsc.edu'
    ftpuser = auth.hosts[encodeftp][0]
    ftppassword = auth.hosts[encodeftp][2]
    context = {'archivename': make_submission_name(ininame),
               'initialdir': os.getcwd(),
               'user': os.getlogin(),
               'ftpuser': ftpuser,
               'ftppassword': ftppassword,
               'ftphost': encodeftp}

    condor_script = make_condor_name(ininame, 'upload')
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

def make_md5sum(filename):
    """Quickly find the md5sum of a file
    """
    md5_cache = os.path.join(filename+".md5")
    print md5_cache
    if os.path.exists(md5_cache):
        logging.debug("Found md5sum in {0}".format(md5_cache))
        stream = open(md5_cache,'r')
        lines = stream.readlines()
        md5sum = parse_md5sum_line(lines, filename)
    else:
        md5sum = make_md5sum_unix(filename, md5_cache)
    return md5sum
    
def make_md5sum_unix(filename, md5_cache):
    cmd = ["md5sum", filename]
    logging.debug("Running {0}".format(" ".join(cmd)))
    p = Popen(cmd, stdout=PIPE)
    stdin, stdout = p.communicate()
    retcode = p.wait()
    logging.debug("Finished {0} retcode {1}".format(" ".join(cmd), retcode))
    if retcode != 0:
        logging.error("Trouble with md5sum for {0}".format(filename))
        return None
    lines = stdin.split(os.linesep)
    md5sum = parse_md5sum_line(lines, filename)
    if md5sum is not None:
        logging.debug("Caching sum in {0}".format(md5_cache))
        stream = open(md5_cache, "w")
        stream.write(stdin)
        stream.close()
    return md5sum

def parse_md5sum_line(lines, filename):
    md5sum, md5sum_filename = lines[0].split()
    if md5sum_filename != filename:
        errmsg = "MD5sum and I disagre about filename. {0} != {1}"
        logging.error(errmsg.format(filename, md5sum_filename))
        return None
    return md5sum

if __name__ == "__main__":
    main()
