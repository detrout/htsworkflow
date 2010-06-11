#!/usr/bin/env python
from ConfigParser import SafeConfigParser
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

def make_submission_name(ininame):
    base = os.path.basename(ininame)
    name, ext = os.path.splitext(base)
    return name + '.tgz'

def make_ddf_name(pathname):
    base = os.path.basename(pathname)
    name, ext = os.path.splitext(base)
    return name + '.ddf'

def make_condor_name(pathname):
    base = os.path.basename(pathname)
    name, ext = os.path.splitext(base)
    return name + '.condor'
    
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
        f = open(target,'w')
    else:
        f = target
    f.write(header)
    for entry in body_list:
        f.write(entry)
    if type(target) in types.StringTypes:
        f.close()

def parse_filelist(file_string):
    return file_string.split(',')

def validate_filelist(files):
    """
    Die if a file doesn't exist in a file list
    """
    for f in files:
        if not os.path.exists(f):
            raise RuntimeError("%s does not exist" % (f,))

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
            
def make_condor_archive_script(ininame, files):
    script = """Universe = vanilla

Executable = /bin/tar
arguments = czvf ../%(archivename)s %(filelist)s

Error = compress.err.$(Process).log
Output = compress.out.$(Process).log
Log = compress.log
initialdir = %(initialdir)s

queue 
"""
    for f in files:
        if not os.path.exists(f):
            raise RuntimeError("Missing %s" % (f,))

    context = {'archivename': make_submission_name(ininame),
               'filelist': " ".join(files),
               'initialdir': os.getcwd()}

    condor_script = make_condor_name(ininame)
    condor_stream = open(condor_script,'w')
    condor_stream.write(script % context)
    condor_stream.close()

def make_ddf(ininame,  daf_name, guess_ddf=False, make_condor=False, outdir=None):
    """
    Make ddf files, and bonus condor file
    """
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
        make_condor_archive_script(ininame, file_list)
        
    os.chdir(curdir)


def get_library_info(host, apidata, library_id):
    url = api.library_url(host, library_id)
    contents = api.retrieve_info(url, apidata)
    return contents
    
def read_library_result_map(filename):
    stream = open(filename,'r')

    results = []
    for line in stream:
        if not line.startswith('#'):
            library_id, result_dir = line.strip().split()
            results.append((library_id, result_dir))
    return results

def condor_srf_to_fastq(srf_file, target_pathname):
    script = """output=%(target_pathname)s
arguments="-c %(srf_file)s"
queue
"""
    params = {'srf_file': srf_file,
              'target_pathname': target_pathname}
    
    return  script % params

def condor_qseq_to_fastq(qseq_file, target_pathname):
    script = """
arguments="-i %(qseq_file)s -o %(target_pathname)s"
queue
"""
    params = {'qseq_file': qseq_file,
              'target_pathname': target_pathname}
    
    return script % params

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
            lanes = lib_info.setdefault('lanes', {})
            lanes.setdefault(lane_key, set()).add(seq)
    
    return lib_db

def build_fastqs(host, apidata, sequences_path, library_result_map, 
                 paired=True ):
    """
    Generate condor scripts to build any needed fastq files
    
    Args:
      host (str): root of the htsworkflow api server
      apidata (dict): id & key to post to the server
      sequences_path (str): root of the directory tree to scan for files
      library_result_map (list):  [(library_id, destination directory), ...]
      paired: should we assume that we are processing paired end records?
              if False, we will treat this as single ended.
    """
    qseq_condor_header = """
Universe=vanilla
executable=/woldlab/rattus/lvol0/mus/home/diane/proj/gaworkflow/scripts/qseq2fastq
error=qseqfastq.err.$(process).log
output=qseqfastq.out.$(process).log
log=qseqfastq.log

"""
    qseq_condor_entries = []
    srf_condor_header = """
Universe=vanilla
executable=/woldlab/rattus/lvol0/mus/home/diane/bin/srf2fastq
output=srf2fastq.out.$(process).log
error=srf2fastq.err.$(process).log
log=srffastq.log

"""
    srf_condor_entries = []
    fastq_paired_template = '%(lib_id)s_%(flowcell)s_c%(cycle)s_l%(lane)s_r%(read)s.fastq'
    fastq_single_template = '%(lib_id)s_%(flowcell)s_c%(cycle)s_l%(lane)s.fastq'
    lib_db = find_archive_sequence_files(host, 
                                         apidata, 
                                         sequences_path, 
                                         library_result_map)

    # find what targets we're missing
    needed_targets = {}
    for lib_id, result_dir in library_result_map:
        lib = lib_db[lib_id]
        for lane_key, sequences in lib['lanes'].items():
            for seq in sequences:
                filename_attributes = { 
                    'flowcell': seq.flowcell,
                    'lib_id': lib_id,
                    'lane': seq.lane,
                    'read': seq.read,
                    'cycle': seq.cycle
                    }
                # throw out test runs
                # FIXME: this should probably be configurable
                if seq.cycle < 50:
                    continue
                if seq.flowcell == '30CUUAAXX':
                    # 30CUUAAXX run sucked
                    continue

                # end filters
                if paired:
                    target_name = fastq_paired_template % filename_attributes
                else:
                    target_name = fastq_single_template % filename_attributes

                target_pathname = os.path.join(result_dir, target_name)
                if not os.path.exists(target_pathname):
                    t = needed_targets.setdefault(target_pathname, {})
                    t[seq.filetype] = seq
                    
    for target_pathname, available_sources in needed_targets.items():
        logging.debug(' target : %s' % (target_pathname,))
        logging.debug(' candidate sources: %s' % (available_sources,))
        if available_sources.has_key('qseq'):
            source = available_sources['qseq']
            qseq_condor_entries.append(
                condor_qseq_to_fastq(source.path, target_pathname)
            )
        elif available_sources.has_key('srf'):
            source = available_sources['srf']
            if source.read is not None:
                logging.warn(
                    "srf -> fastq paired end doesn't work yet: %s" % (source,)
                )
            else:
                srf_condor_entries.append(
                    condor_srf_to_fastq(source.path, target_pathname)
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

def find_best_extension(extension_map, filename):
    """
    Search through extension_map looking for the best extension
    The 'best' is the longest match

    :Args:
      extension_map (dict): '.ext' -> { 'view': 'name' or None }
      filename (str): the filename whose extention we are about to examine
    """
    best_ext = None
    path, last_ext = os.path.splitext(filename)

    for ext in extension_map.keys():
        if filename.endswith(ext):
            if best_ext is None:
                best_ext = ext
            elif len(ext) > len(best_ext):
                best_ext = ext
    return best_ext

def make_submission_section(line_counter, files, standard_attributes, file_attributes):
    """
    Create a section in the submission ini file
    """
    inifile = [ '[line%s]' % (line_counter,) ]
    inifile += ["files=%s" % (",".join(files))]
    cur_attributes = {}
    cur_attributes.update(standard_attributes)
    cur_attributes.update(file_attributes)
    
    for k,v in cur_attributes.items():
        inifile += ["%s=%s" % (k,v)]
    return inifile
    
def make_submission_ini(host, apidata, library_result_map):
    attributes = {
        '.bai':                   {'view': None}, # bam index
        '.bam':                   {'view': 'Signal'},
        '.splices.bam':           {'view': 'Splices'},
        '.bed':                   {'view': 'TopHatJunctions'},
        '.bigwig':                {'view': 'RawSigna'},
        '.tar.bz2':               {'view': None},
        '.condor':                {'view': None},
        '.daf':                   {'view': None},
        '.ddf':                   {'view': None},
        'novel.genes.expr':       {'view': 'GeneDeNovoFPKM'},
        'novel.transcripts.expr': {'view': 'TranscriptDeNovoFPKM'},
        '.genes.expr':            {'view': 'GeneFPKM'},
        '.transcripts.expr':      {'view': 'TranscriptFPKM'},
        '.fastq':                 {'view': 'Fastq' },
        '_r1.fastq':              {'view': 'FastqRd1'},
        '_r2.fastq':              {'view': 'FastqRd2'},
        '.gtf':                   {'view': 'CufflinksGeneModel'},
        '.ini':                   {'view': None},
        '.log':                   {'view': None},
        '.stats.txt':             {'view': 'InsLength'},
        '.srf':                   {'view': None},
        '.wig':                   {'view': 'RawSignal'},
    }
   
    candidate_fastq_src = {}

    for lib_id, result_dir in library_result_map:
        inifile =  ['[config]']
        inifile += ['order_by=files view cell localization rnaExtract mapAlgorithm readType replicate labVersion']
        inifile += ['']
        line_counter = 1
        lib_info = get_library_info(host, apidata, lib_id)
        result_ini = os.path.join(result_dir, result_dir+'.ini')

        if lib_info['cell_line'].lower() == 'unknown':
            logging.warn("Library %s missing cell_line" % (lib_id,))

        standard_attributes = {'cell': lib_info['cell_line'],
                               'insertLength': '200', 
                               'labVersion': 'TopHat',
                               'localization': 'cell',
                               'mapAlgorithm': 'TopHat',
                               'readType': '2x75', 
                               'replicate': lib_info['replicate'],
                               'rnaExtract': 'longPolyA',
                               }

        # write other lines
        submission_files = os.listdir(result_dir)
        fastqs = {}
        for f in submission_files:
            best_ext = find_best_extension(attributes, f)

            if best_ext is not None:
               if attributes[best_ext]['view'] is None:
                   
                   continue
               elif best_ext.endswith('fastq'):
                   fastqs.setdefault(best_ext, set()).add(f)
               else:
                   inifile.extend(
                       make_submission_section(line_counter,
                                               [f],
                                               standard_attributes,
                                               attributes[best_ext]
                                               )
                       )
                   inifile += ['']
                   line_counter += 1
            else:
                raise ValueError("Unrecognized file: %s" % (f,))

        # add in fastqs on a single line.
        for extension, fastq_set in fastqs.items():
            inifile.extend(
                make_submission_section(line_counter, 
                                        fastq_set,
                                        standard_attributes,
                                        attributes[extension])
            )
            inifile += ['']
            line_counter += 1
            
        f = open(result_ini,'w')
        f.write(os.linesep.join(inifile))

def link_daf(daf_path, library_result_map):
    if not os.path.exists(daf_path):
        raise RuntimeError("%s does not exist, how can I link to it?" % (daf_path,))

    base_daf = os.path.basename(daf_path)
    
    for lib_id, result_dir in library_result_map:
        submission_daf = os.path.join(result_dir, base_daf)
        if not os.path.exists(submission_daf):
            os.link(daf_path, submission_daf)

def make_all_ddfs(library_result_map, daf_name):
    for lib_id, result_dir in library_result_map:
        ininame = result_dir+'.ini'
        inipathname = os.path.join(result_dir, ininame)
        if os.path.exists(inipathname):
            make_ddf(ininame, daf_name, True, True, result_dir)
            
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
    parser.add_option('--fastq', help="generate scripts for making fastq files",
                      default=False, action="store_true")

    parser.add_option('--ini', help="generate submission ini file", default=False,
                      action="store_true")

    parser.add_option('--makeddf', help='make the ddfs', default=False,
                      action="store_true")
    
    parser.add_option('--daf', default=None, help='specify daf name')

    # configuration options
    parser.add_option('--apiid', default=apiid, help="Specify API ID")
    parser.add_option('--apikey', default=apikey, help="Specify API KEY")
    parser.add_option('--host',  default=apihost,
                      help="specify HTSWorkflow host",)
    parser.add_option('--sequence', default=sequence_archive,
                      help="sequence repository")
    parser.add_option('--single', default=False, action="store_true", 
                      help="treat the sequences as single ended runs")

    # debugging
    parser.add_option('--verbose', default=False, action="store_true",
                      help='verbose logging')
    parser.add_option('--debug', default=False, action="store_true",
                      help='debug logging')

    return parser

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

    if opts.daf is not None:
        link_daf(opts.daf, library_result_map)

    if opts.fastq:
        build_fastqs(opts.host, 
                     apidata, 
                     opts.sequence, 
                     library_result_map,
                     not opts.single)

    if opts.ini:
        make_submission_ini(opts.host, apidata, library_result_map)

    if opts.makeddf:
        make_all_ddfs(library_result_map, opts.daf)
        
if __name__ == "__main__":
    main()
