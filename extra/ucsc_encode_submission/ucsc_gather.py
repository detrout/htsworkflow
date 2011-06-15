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
from htsworkflow.submission.condorfastq import CondorFastqExtract

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

    if opts.makeddf and opts.daf is None:
        parser.error("Please specify your daf when making ddf files")

    if len(args) == 0:
        parser.error("I need at least one library submission-dir input file")
        
    library_result_map = []
    for a in args:
        library_result_map.extend(read_library_result_map(a))

    if opts.make_tree_from is not None:
        make_tree_from(opts.make_tree_from, library_result_map)
            
    if opts.daf is not None:
        link_daf(opts.daf, library_result_map)

    if opts.fastq:
        extractor = CondorFastqExtract(opts.host, apidata, opts.sequence,
                                       force=opts.force)
        extractor.build_fastqs(library_result_map)

    if opts.ini:
        make_submission_ini(opts.host, apidata, library_result_map)

    if opts.makeddf:
        make_all_ddfs(library_result_map, opts.daf, force=opts.force)


def make_parser():
    parser = OptionParser()

    # commands
    parser.add_option('--make-tree-from',
                      help="create directories & link data files",
                      default=None)
    parser.add_option('--fastq', help="generate scripts for making fastq files",
                      default=False, action="store_true")

    parser.add_option('--ini', help="generate submission ini file", default=False,
                      action="store_true")

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


def make_submission_ini(host, apidata, library_result_map, paired=True):
    #attributes = get_filename_attribute_map(paired)
    view_map = NameToViewMap(host, apidata)
    
    candidate_fastq_src = {}

    for lib_id, result_dir in library_result_map:
        order_by = ['order_by=files', 'view', 'replicate', 'cell', 
                    'readType', 'mapAlgorithm', 'insertLength', 'md5sum' ]
        inifile =  ['[config]']
        inifile += [" ".join(order_by)]
        inifile += ['']
        line_counter = 1
        result_ini = os.path.join(result_dir, result_dir+'.ini')

        # write other lines
        submission_files = os.listdir(result_dir)
        fastqs = {}
        fastq_attributes = {}
        for f in submission_files:
            attributes = view_map.find_attributes(f, lib_id)
            if attributes is None:
                raise ValueError("Unrecognized file: %s" % (f,))
            attributes['md5sum'] = "None"
            
            ext = attributes["extension"]
            if attributes['view'] is None:                   
                continue               
            elif attributes.get("type", None) == 'fastq':
                fastqs.setdefault(ext, set()).add(f)
                fastq_attributes[ext] = attributes
            else:
                md5sum = make_md5sum(os.path.join(result_dir,f))
                if md5sum is not None:
                    attributes['md5sum']=md5sum
                inifile.extend(
                    make_submission_section(line_counter,
                                            [f],
                                            attributes
                                            )
                    )
                inifile += ['']
                line_counter += 1
                # add in fastqs on a single line.

        for extension, fastq_files in fastqs.items():
            inifile.extend(
                make_submission_section(line_counter, 
                                        fastq_files,
                                        fastq_attributes[extension])
            )
            inifile += ['']
            line_counter += 1
            
        f = open(result_ini,'w')
        f.write(os.linesep.join(inifile))

        
def make_all_ddfs(library_result_map, daf_name, make_condor=True, force=False):
    dag_fragment = []
    for lib_id, result_dir in library_result_map:
        ininame = result_dir+'.ini'
        inipathname = os.path.join(result_dir, ininame)
        if os.path.exists(inipathname):
            dag_fragment.extend(
                make_ddf(ininame, daf_name, True, make_condor, result_dir)
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
            

def make_ddf(ininame,  daf_name, guess_ddf=False, make_condor=False, outdir=None):
    """
    Make ddf files, and bonus condor file
    """
    dag_fragments = []
    curdir = os.getcwd()
    if outdir is not None:
        os.chdir(outdir)
    output = sys.stdout
    ddf_name = None
    if guess_ddf:
        ddf_name = make_ddf_name(ininame)
        print ddf_name
        output = open(ddf_name,'w')

    file_list = read_ddf_ini(ininame, output)
    logging.info(
        "Read config {0}, found files: {1}".format(
            ininame, ", ".join(file_list)))

    file_list.append(daf_name)
    if ddf_name is not None:
        file_list.append(ddf_name)

    if make_condor:
        archive_condor = make_condor_archive_script(ininame, file_list)
        upload_condor = make_condor_upload_script(ininame)
        
        dag_fragments.extend( 
            make_dag_fragment(ininame, archive_condor, upload_condor)
        ) 
        
    os.chdir(curdir)
    
    return dag_fragments


def read_ddf_ini(filename, output=sys.stdout):
    """
    Read a ini file and dump out a tab delmited text file
    """
    file_list = []
    config = SafeConfigParser()
    config.read(filename)

    order_by = shlex.split(config.get("config", "order_by"))

    output.write("\t".join(order_by))
    output.write(os.linesep)
    sections = config.sections()
    sections.sort()
    for section in sections:
        if section == "config":
            # skip the config block
            continue
        values = []
        for key in order_by:
            v = config.get(section, key)
            values.append(v)
            if key == 'files':
                file_list.extend(parse_filelist(v))
                
        output.write("\t".join(values))
        output.write(os.linesep)
    return file_list


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


class NameToViewMap(object):
    """Determine view attributes for a given submission file name
    """
    def __init__(self, root_url, apidata):
        self.root_url = root_url
        self.apidata = apidata
        
        self.lib_cache = {}
        self.lib_paired = {}
        # ma is "map algorithm"
        ma = 'TH1014'

        self.patterns = [
            # for 2011 Feb 18 elements submission
            ('final_Cufflinks_genes_*gtf',       'GeneDeNovo'),
            ('final_Cufflinks_transcripts_*gtf', 'TranscriptDeNovo'),
            ('final_exonFPKM-Cufflinks-0.9.3-GENCODE-v3c-*.gtf',       
             'ExonsGencV3c'),
            ('final_GENCODE-v3-Cufflinks-0.9.3.genes-*gtf',          
             'GeneGencV3c'),
            ('final_GENCODE-v3-Cufflinks-0.9.3.transcripts-*gtf',    
             'TranscriptGencV3c'),
            ('final_TSS-Cufflinks-0.9.3-GENCODE-v3c-*.gtf', 'TSS'),
            ('final_junctions-*.bed6+3',                    'Junctions'),
            
            ('*.bai',                   None),
            ('*.splices.bam',           'Splices'),
            ('*.bam',                   self._guess_bam_view),
            ('junctions.bed',           'Junctions'),
            ('*.jnct',                  'Junctions'),
            ('*unique.bigwig',         None),
            ('*plus.bigwig',           'PlusSignal'),
            ('*minus.bigwig',          'MinusSignal'),
            ('*.bigwig',                'Signal'),
            ('*.tar.bz2',               None),
            ('*.condor',                None),
            ('*.daf',                   None),
            ('*.ddf',                   None),

            ('*ufflinks?0.9.3.genes.gtf',       'GeneDeNovo'),
            ('*ufflinks?0.9.3.transcripts.gtf', 'TranscriptDeNovo'),
            ('*GENCODE-v3c.exonFPKM.gtf',        'ExonsGencV3c'),
            ('*GENCODE-v3c.genes.gtf',           'GeneGencV3c'),
            ('*GENCODE-v3c.transcripts.gtf',     'TranscriptGencV3c'),
            ('*GENCODE-v3c.TSS.gtf',             'TSS'),
            ('*.junctions.bed6+3',                'Junctions'),
            
            ('*.?ufflinks-0.9.0?genes.expr',       'GeneDeNovo'),
            ('*.?ufflinks-0.9.0?transcripts.expr', 'TranscriptDeNovo'),
            ('*.?ufflinks-0.9.0?transcripts.gtf',  'GeneModel'),

            ('*.GENCODE-v3c?genes.expr',       'GeneGCV3c'),
            ('*.GENCODE-v3c?transcript*.expr', 'TranscriptGCV3c'),
            ('*.GENCODE-v3c?transcript*.gtf',  'TranscriptGencV3c'),
            ('*.GENCODE-v4?genes.expr',        None), #'GeneGCV4'),
            ('*.GENCODE-v4?transcript*.expr',  None), #'TranscriptGCV4'),
            ('*.GENCODE-v4?transcript*.gtf',   None), #'TranscriptGencV4'),
            ('*_1.75mers.fastq',              'FastqRd1'),
            ('*_2.75mers.fastq',              'FastqRd2'),
            ('*_r1.fastq',              'FastqRd1'),
            ('*_r2.fastq',              'FastqRd2'),
            ('*.fastq',                 'Fastq'),
            ('*.gtf',                   'GeneModel'),
            ('*.ini',                   None),
            ('*.log',                   None),
            ('*.md5',                   None),
            ('paired-end-distribution*', 'InsLength'),
            ('*.stats.txt',              'InsLength'),
            ('*.srf',                   None),
            ('*.wig',                   None),
            ('*.zip',                   None),
            ('transfer_log',            None),
            ]

        self.views = {
            None: {"MapAlgorithm": "NA"},
            "Paired": {"MapAlgorithm": ma},
            "Aligns": {"MapAlgorithm": ma},
            "Single": {"MapAlgorithm": ma},
            "Splices": {"MapAlgorithm": ma},
            "Junctions": {"MapAlgorithm": ma},
            "PlusSignal": {"MapAlgorithm": ma},
            "MinusSignal": {"MapAlgorithm": ma},
            "Signal": {"MapAlgorithm": ma},
            "GeneModel": {"MapAlgorithm": ma},
            "GeneDeNovo": {"MapAlgorithm": ma},
            "TranscriptDeNovo": {"MapAlgorithm": ma},
            "ExonsGencV3c": {"MapAlgorithm": ma},
            "GeneGencV3c": {"MapAlgorithm": ma},
            "TSS": {"MapAlgorithm": ma},
            "GeneGCV3c": {"MapAlgorithm": ma},
            "TranscriptGCV3c": {"MapAlgorithm": ma},
            "TranscriptGencV3c": {"MapAlgorithm": ma},
            "GeneGCV4": {"MapAlgorithm": ma},
            "TranscriptGCV4": {"MapAlgorithm": ma},
            "FastqRd1": {"MapAlgorithm": "NA", "type": "fastq"},
            "FastqRd2": {"MapAlgorithm": "NA", "type": "fastq"},
            "Fastq": {"MapAlgorithm": "NA", "type": "fastq" },
            "InsLength": {"MapAlgorithm": ma},
            }
        # view name is one of the attributes
        for v in self.views.keys():
            self.views[v]['view'] = v
            
    def find_attributes(self, pathname, lib_id):
        """Looking for the best extension
        The 'best' is the longest match
        
        :Args:
        filename (str): the filename whose extention we are about to examine
        """
        path, filename = os.path.splitext(pathname)
        if not self.lib_cache.has_key(lib_id):
            self.lib_cache[lib_id] = get_library_info(self.root_url,
                                                      self.apidata, lib_id)

        lib_info = self.lib_cache[lib_id]
        if lib_info['cell_line'].lower() == 'unknown':
            logging.warn("Library %s missing cell_line" % (lib_id,))
        attributes = {
            'cell': lib_info['cell_line'],
            'replicate': lib_info['replicate'],
            }
        is_paired = self._is_paired(lib_id, lib_info)
        
        if is_paired:
            attributes.update(self.get_paired_attributes(lib_info))
        else:
            attributes.update(self.get_single_attributes(lib_info))
            
        for pattern, view in self.patterns:
            if fnmatch.fnmatch(pathname, pattern):
                if callable(view):
                    view = view(is_paired=is_paired)
                    
                attributes.update(self.views[view])
                attributes["extension"] = pattern
                return attributes


    def _guess_bam_view(self, is_paired=True):
        """Guess a view name based on library attributes
        """
        if is_paired:
            return "Paired"
        else:
            return "Aligns"


    def _is_paired(self, lib_id, lib_info):
        """Determine if a library is paired end"""
        # TODO: encode this information in the library type page.
        single = (1,3,6)
        if len(lib_info["lane_set"]) == 0:
            # we haven't sequenced anything so guess based on library type
            if lib_info['library_type_id'] in single:
                return False
            else:
                return True

        if not self.lib_paired.has_key(lib_id):
            is_paired = 0
            isnot_paired = 0
            failed = 0
            # check to see if all the flowcells are the same.
            # otherwise we might need to do something complicated
            for flowcell in lib_info["lane_set"]:
                # yes there's also a status code, but this comparison 
                # is easier to read
                if flowcell["status"].lower() == "failed":
                    # ignore failed flowcell
                    failed += 1
                    pass
                elif flowcell["paired_end"]:
                    is_paired += 1
                else:
                    isnot_paired += 1
                    
            logging.debug("Library %s: %d paired, %d single, %d failed" % \
                     (lib_info["library_id"], is_paired, isnot_paired, failed))

            if is_paired > isnot_paired:
                self.lib_paired[lib_id] = True
            elif is_paired < isnot_paired:
                self.lib_paired[lib_id] = False
            else:
                raise RuntimeError("Equal number of paired & unpaired lanes."\
                                   "Can't guess library paired status")
            
        return self.lib_paired[lib_id]

    def get_paired_attributes(self, lib_info):
        if lib_info['insert_size'] is None:
            errmsg = "Library %s is missing insert_size, assuming 200"
            logging.warn(errmsg % (lib_info["library_id"],))
            insert_size = 200
        else:
            insert_size = lib_info['insert_size']
        return {'insertLength': insert_size,
                'readType': '2x75'}

    def get_single_attributes(self, lib_info):
        return {'insertLength':'ilNA',
                'readType': '1x75D'
                }

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
