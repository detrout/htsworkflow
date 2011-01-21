#!/usr/bin/env python
from ConfigParser import SafeConfigParser
import fnmatch
from glob import glob
import json
import logging
from optparse import OptionParser
import os
from pprint import pprint, pformat
import shlex
from StringIO import StringIO
import time
import sys
import types
import urllib
import urllib2
import urlparse

from htsworkflow.util import api
from htsworkflow.pipelines.sequences import \
    create_sequence_table, \
    scan_for_sequences
from htsworkflow.pipelines import qseq2fastq
from htsworkflow.pipelines import srf2fastq

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    
    if opts.debug:
        logging.basicConfig(level = logging.DEBUG )
    elif opts.verbose:
        logging.basicConfig(level = logging.INFO )
    else:
        logging.basicConfig(level = logging.WARNING )        
    
    apidata = {'apiid': opts.apiid, 'apikey': opts.apikey }

    if opts.host is None or opts.apiid is None or opts.apikey is None:
        parser.error("Please specify host url, apiid, apikey")

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
        build_fastqs(opts.host, 
                     apidata, 
                     opts.sequence, 
                     library_result_map,
                     force=opts.force)

    if opts.ini:
        make_submission_ini(opts.host, apidata, library_result_map)

    if opts.makeddf:
        make_all_ddfs(library_result_map, opts.daf, force=opts.force)


def make_parser():
    # Load defaults from the config files
    config = SafeConfigParser()
    config.read([os.path.expanduser('~/.htsworkflow.ini'), '/etc/htsworkflow.ini'])
    
    sequence_archive = None
    apiid = None
    apikey = None
    apihost = None
    SECTION = 'sequence_archive'
    if config.has_section(SECTION):
        sequence_archive = config.get(SECTION, 'sequence_archive',sequence_archive)
        sequence_archive = os.path.expanduser(sequence_archive)
        apiid = config.get(SECTION, 'apiid', apiid)
        apikey = config.get(SECTION, 'apikey', apikey)
        apihost = config.get(SECTION, 'host', apihost)

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

    # configuration options
    parser.add_option('--apiid', default=apiid, help="Specify API ID")
    parser.add_option('--apikey', default=apikey, help="Specify API KEY")
    parser.add_option('--host',  default=apihost,
                      help="specify HTSWorkflow host",)
    parser.add_option('--sequence', default=sequence_archive,
                      help="sequence repository")

    # debugging
    parser.add_option('--verbose', default=False, action="store_true",
                      help='verbose logging')
    parser.add_option('--debug', default=False, action="store_true",
                      help='debug logging')

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
    
def build_fastqs(host, apidata, sequences_path, library_result_map, 
                 force=False ):
    """
    Generate condor scripts to build any needed fastq files
    
    Args:
      host (str): root of the htsworkflow api server
      apidata (dict): id & key to post to the server
      sequences_path (str): root of the directory tree to scan for files
      library_result_map (list):  [(library_id, destination directory), ...]
    """
    qseq_condor_header = """
Universe=vanilla
executable=%(exe)s
error=log/qseq2fastq.err.$(process).log
output=log/qseq2fastq.out.$(process).log
log=log/qseq2fastq.log

""" % {'exe': sys.executable }
    qseq_condor_entries = []
    srf_condor_header = """
Universe=vanilla
executable=%(exe)s
output=log/srf_pair_fastq.out.$(process).log
error=log/srf_pair_fastq.err.$(process).log
log=log/srf_pair_fastq.log
environment="PYTHONPATH=/home/diane/lib/python2.6/site-packages:/home/diane/proj/solexa/gaworkflow PATH=/woldlab/rattus/lvol0/mus/home/diane/bin:/usr/bin:/bin"

""" % {'exe': sys.executable }
    srf_condor_entries = []
    lib_db = find_archive_sequence_files(host, 
                                         apidata, 
                                         sequences_path, 
                                         library_result_map)

    needed_targets = find_missing_targets(library_result_map, lib_db, force)

    for target_pathname, available_sources in needed_targets.items():
        logging.debug(' target : %s' % (target_pathname,))
        logging.debug(' candidate sources: %s' % (available_sources,))
        if available_sources.has_key('qseq'):
            source = available_sources['qseq']
            qseq_condor_entries.append(
                condor_qseq_to_fastq(source.path, 
                                     target_pathname, 
                                     source.flowcell,
                                     force=force)
            )
        elif available_sources.has_key('srf'):
            source = available_sources['srf']
            mid = getattr(source, 'mid_point', None)
            srf_condor_entries.append(
                condor_srf_to_fastq(source.path, 
                                    target_pathname,
                                    source.paired,
                                    source.flowcell,
                                    mid,
                                    force=force)
            )
        else:
            print " need file", target_pathname

    if len(srf_condor_entries) > 0:
        make_submit_script('srf.fastq.condor', 
                           srf_condor_header,
                           srf_condor_entries)

    if len(qseq_condor_entries) > 0:
        make_submit_script('qseq.fastq.condor', 
                           qseq_condor_header,
                           qseq_condor_entries)


def find_missing_targets(library_result_map, lib_db, force=False):
    """
    Check if the sequence file exists.
    This requires computing what the sequence name is and checking
    to see if it can be found in the sequence location.

    Adds seq.paired flag to sequences listed in lib_db[*]['lanes']
    """
    fastq_paired_template = '%(lib_id)s_%(flowcell)s_c%(cycle)s_l%(lane)s_r%(read)s.fastq'
    fastq_single_template = '%(lib_id)s_%(flowcell)s_c%(cycle)s_l%(lane)s.fastq'
    # find what targets we're missing
    needed_targets = {}
    for lib_id, result_dir in library_result_map:
        lib = lib_db[lib_id]
        lane_dict = make_lane_dict(lib_db, lib_id)
        
        for lane_key, sequences in lib['lanes'].items():
            for seq in sequences:
                seq.paired = lane_dict[seq.flowcell]['paired_end']
                lane_status = lane_dict[seq.flowcell]['status']

                if seq.paired and seq.read is None:
                    seq.read = 1
                filename_attributes = { 
                    'flowcell': seq.flowcell,
                    'lib_id': lib_id,
                    'lane': seq.lane,
                    'read': seq.read,
                    'cycle': seq.cycle
                    }
                # skip bad runs
                if lane_status == 'Failed':
                    continue
                if seq.flowcell == '30DY0AAXX':
                    # 30DY0 only ran for 151 bases instead of 152
                    # it is actually 76 1st read, 75 2nd read
                    seq.mid_point = 76

                # end filters
                if seq.paired:
                    target_name = fastq_paired_template % filename_attributes
                else:
                    target_name = fastq_single_template % filename_attributes

                target_pathname = os.path.join(result_dir, target_name)
                if force or not os.path.exists(target_pathname):
                    t = needed_targets.setdefault(target_pathname, {})
                    t[seq.filetype] = seq

    return needed_targets


def link_daf(daf_path, library_result_map):
    if not os.path.exists(daf_path):
        raise RuntimeError("%s does not exist, how can I link to it?" % (daf_path,))

    base_daf = os.path.basename(daf_path)
    
    for lib_id, result_dir in library_result_map:
        submission_daf = os.path.join(result_dir, base_daf)
        if not os.path.exists(submission_daf):
            os.link(daf_path, submission_daf)


def make_submission_ini(host, apidata, library_result_map, paired=True):
    #attributes = get_filename_attribute_map(paired)
    view_map = NameToViewMap(host, apidata)
    
    candidate_fastq_src = {}

    for lib_id, result_dir in library_result_map:
        order_by = ['order_by=files', 'view', 'replicate', 'cell', 
                    'readType', 'mapAlgorithm', 'insertLength' ]
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
            
            ext = attributes["extension"]
            if attributes['view'] is None:                   
                continue               
            elif attributes.get("type", None) == 'fastq':
                fastqs.setdefault(ext, set()).add(f)
                fastq_attributes[ext] = attributes
            else:
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

        
def make_lane_dict(lib_db, lib_id):
    """
    Convert the lane_set in a lib_db to a dictionary
    indexed by flowcell ID
    """
    result = []
    for lane in lib_db[lib_id]['lane_set']:
        result.append((lane['flowcell'], lane))
    return dict(result)


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
arguments = -c put ../%(archivename)s -o ftp://detrout@encodeftp.cse.ucsc.edu/%(archivename)s

Error = upload.err.$(Process).log
Output = upload.out.$(Process).log
Log = /tmp/submission-upload-%(user)s.log
initialdir = %(initialdir)s

queue 
"""
    context = {'archivename': make_submission_name(ininame),
               'initialdir': os.getcwd(),
               'user': os.getlogin()}

    condor_script = make_condor_name(ininame, 'upload')
    condor_stream = open(condor_script,'w')
    condor_stream.write(script % context)
    condor_stream.close()
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


def condor_srf_to_fastq(srf_file, target_pathname, paired, flowcell=None,
                        mid=None, force=False):
    py = srf2fastq.__file__
    args = [ py, srf_file, ]
    if paired:
        args.extend(['--left', target_pathname])
        # this is ugly. I did it because I was pregenerating the target
        # names before I tried to figure out what sources could generate
        # those targets, and everything up to this point had been
        # one-to-one. So I couldn't figure out how to pair the 
        # target names. 
        # With this at least the command will run correctly.
        # however if we rename the default targets, this'll break
        # also I think it'll generate it twice.
        args.extend(['--right', 
                     target_pathname.replace('_r1.fastq', '_r2.fastq')])
    else:
        args.extend(['--single', target_pathname ])
    if flowcell is not None:
        args.extend(['--flowcell', flowcell])

    if mid is not None:
        args.extend(['-m', str(mid)])

    if force:
        args.extend(['--force'])

    script = """
arguments="%s"
queue
""" % (" ".join(args),)
    
    return  script 


def condor_qseq_to_fastq(qseq_file, target_pathname, flowcell=None, force=False):
    py = qseq2fastq.__file__
    args = [py, '-i', qseq_file, '-o', target_pathname ]
    if flowcell is not None:
        args.extend(['-f', flowcell])
    script = """
arguments="%s"
queue
""" % (" ".join(args))

    return script 

def find_archive_sequence_files(host, apidata, sequences_path, 
                                library_result_map):
    """
    Find all the archive sequence files possibly associated with our results.

    """
    logging.debug("Searching for sequence files in: %s" %(sequences_path,))

    lib_db = {}
    seq_dirs = set()
    #seq_dirs = set(os.path.join(sequences_path, 'srfs'))
    candidate_lanes = {}
    for lib_id, result_dir in library_result_map:
        lib_info = get_library_info(host, apidata, lib_id)
        lib_info['lanes'] = {}
        lib_db[lib_id] = lib_info

        for lane in lib_info['lane_set']:
            lane_key = (lane['flowcell'], lane['lane_number'])
            candidate_lanes[lane_key] = lib_id
            seq_dirs.add(os.path.join(sequences_path, 
                                         'flowcells', 
                                         lane['flowcell']))
    logging.debug("Seq_dirs = %s" %(unicode(seq_dirs)))
    candidate_seq_list = scan_for_sequences(seq_dirs)

    # at this point we have too many sequences as scan_for_sequences
    # returns all the sequences in a flowcell directory
    # so lets filter out the extras
    
    for seq in candidate_seq_list:
        lane_key = (seq.flowcell, seq.lane)
        lib_id = candidate_lanes.get(lane_key, None)
        if lib_id is not None:
            lib_info = lib_db[lib_id]
            lib_info['lanes'].setdefault(lane_key, set()).add(seq)
    
    return lib_db


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
            ('*.bai',                   None),
            ('*.splices.bam',           'Splices'),
            ('*.bam',                   self._guess_bam_view),
            ('junctions.bed',           'Junctions'),
            ('*.jnct',                  'Junctions'),
            ('*.unique.bigwig',         None),
            ('*.plus.bigwig',           'PlusSignal'),
            ('*.minus.bigwig',          'MinusSignal'),
            ('*.bigwig',                'Signal'),
            ('*.tar.bz2',               None),
            ('*.condor',                None),
            ('*.daf',                   None),
            ('*.ddf',                   None),
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
            ('paired-end-distribution*', 'InsLength'),
            ('*.stats.txt',              'InsLength'),
            ('*.srf',                   None),
            ('*.wig',                   None),
            ('*.zip',                   None),
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
        if len(lib_info["lane_set"]) == 0:
            return False

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


def make_submit_script(target, header, body_list):
    """
    write out a text file

    this was intended for condor submit scripts

    Args:
      target (str or stream): 
        if target is a string, we will open and close the file
        if target is a stream, the caller is responsible.

      header (str);
        header to write at the beginning of the file
      body_list (list of strs):
        a list of blocks to add to the file.
    """
    if type(target) in types.StringTypes:
        f = open(target,"w")
    else:
        f = target
    f.write(header)
    for entry in body_list:
        f.write(entry)
    if type(target) in types.StringTypes:
        f.close()

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
