"""Convert srf and qseq archive files to fastqs
"""
import logging
import os
import sys
import types

from htsworkflow.pipelines.sequences import scan_for_sequences
from htsworkflow.pipelines import qseq2fastq
from htsworkflow.pipelines import srf2fastq
from htsworkflow.util.api import HtswApi
from htsworkflow.util.conversion import parse_flowcell_id

logger = logging.getLogger(__name__)

class CondorFastqExtract(object):
    def __init__(self, host, apidata, sequences_path,
                 log_path='log',
                 force=False):
        """Extract fastqs from results archive

        Args:
          host (str): root of the htsworkflow api server
          apidata (dict): id & key to post to the server
          sequences_path (str): root of the directory tree to scan for files
          log_path (str): where to put condor log files
          force (bool): do we force overwriting current files?
        """
        self.api = HtswApi(host, apidata)
        self.sequences_path = sequences_path
        self.log_path = log_path
        self.force = force

    def build_fastqs(self, library_result_map ):
        """
        Generate condor scripts to build any needed fastq files
        
        Args:
          library_result_map (list):  [(library_id, destination directory), ...]
        """
        qseq_condor_header = self.get_qseq_condor_header()
        qseq_condor_entries = []
        srf_condor_header = self.get_srf_condor_header()
        srf_condor_entries = []
        lib_db = self.find_archive_sequence_files(library_result_map)
    
        needed_targets = self.find_missing_targets(library_result_map, lib_db)
    
        for target_pathname, available_sources in needed_targets.items():
            logger.debug(' target : %s' % (target_pathname,))
            logger.debug(' candidate sources: %s' % (available_sources,))
            if available_sources.has_key('qseq'):
                source = available_sources['qseq']
                qseq_condor_entries.append(
                    self.condor_qseq_to_fastq(source.path, 
                                              target_pathname, 
                                              source.flowcell)
                )
            elif available_sources.has_key('srf'):
                source = available_sources['srf']
                mid = getattr(source, 'mid_point', None)
                srf_condor_entries.append(
                    self.condor_srf_to_fastq(source.path, 
                                             target_pathname,
                                             source.paired,
                                             source.flowcell,
                                             mid)
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
    

    def get_qseq_condor_header(self):
        return """Universe=vanilla
executable=%(exe)s
error=%(log)s/qseq2fastq.$(process).out
output=%(log)s/qseq2fastq.$(process).out
log=%(log)s/qseq2fastq.log

""" % {'exe': sys.executable,
       'log': self.log_path }

    def get_srf_condor_header(self):
        return """Universe=vanilla
executable=%(exe)s
output=%(log)s/srf_pair_fastq.$(process).out
error=%(log)s/srf_pair_fastq.$(process).out
log=%(log)s/srf_pair_fastq.log
environment="PYTHONPATH=%(env)s"
    
""" % {'exe': sys.executable,
           'log': self.log_path,
           'env': os.environ.get('PYTHONPATH', '')
      }
            
    def find_archive_sequence_files(self,  library_result_map):
        """
        Find archived sequence files associated with our results.
        """
        logger.debug("Searching for sequence files in: %s" %(self.sequences_path,))
    
        lib_db = {}
        seq_dirs = set()
        candidate_lanes = {}
        for lib_id, result_dir in library_result_map:
            lib_info = self.api.get_library(lib_id)
            lib_info['lanes'] = {}
            lib_db[lib_id] = lib_info
    
            for lane in lib_info['lane_set']:
                lane_key = (lane['flowcell'], lane['lane_number'])
                candidate_lanes[lane_key] = lib_id
                seq_dirs.add(os.path.join(self.sequences_path, 
                                             'flowcells', 
                                             lane['flowcell']))
        logger.debug("Seq_dirs = %s" %(unicode(seq_dirs)))
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
    
    def find_missing_targets(self, library_result_map, lib_db):
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
                    if self.force or not os.path.exists(target_pathname):
                        t = needed_targets.setdefault(target_pathname, {})
                        t[seq.filetype] = seq
    
        return needed_targets

    
    def condor_srf_to_fastq(self,
                            srf_file,
                            target_pathname,
                            paired,
                            flowcell=None,
                            mid=None):
        py = srf2fastq.__file__
        args = [ py, srf_file, '--verbose']
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
    
        if self.force:
            args.extend(['--force'])
    
        script = """arguments="%s"
queue
""" % (" ".join(args),)
        
        return  script 
    
    
    def condor_qseq_to_fastq(self, qseq_file, target_pathname, flowcell=None):
        py = qseq2fastq.__file__
        args = [py, '-i', qseq_file, '-o', target_pathname ]
        if flowcell is not None:
            args.extend(['-f', flowcell])
        script = """arguments="%s"
queue
""" % (" ".join(args))
    
        return script 
    
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

def make_lane_dict(lib_db, lib_id):
    """
    Convert the lane_set in a lib_db to a dictionary
    indexed by flowcell ID
    """
    result = []
    for lane in lib_db[lib_id]['lane_set']:
        flowcell_id, status = parse_flowcell_id(lane['flowcell'])
        lane['flowcell'] = flowcell_id
        result.append((lane['flowcell'], lane))
    return dict(result)

