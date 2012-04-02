"""Convert srf and qseq archive files to fastqs
"""
import logging
import os
from pprint import pformat
import sys
import types

from htsworkflow.pipelines.sequences import scan_for_sequences
from htsworkflow.pipelines import qseq2fastq
from htsworkflow.pipelines import srf2fastq
from htsworkflow.pipelines import desplit_fastq
from htsworkflow.util.api import HtswApi
from htsworkflow.util.conversion import parse_flowcell_id

from django.conf import settings
from django.template import Context, loader

LOGGER = logging.getLogger(__name__)

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

    def create_scripts(self, result_map ):
        """
        Generate condor scripts to build any needed fastq files

        Args:
          result_map: htsworkflow.submission.results.ResultMap()
        """
        template_map = {'srf': 'srf.condor',
                        'qseq': 'qseq.condor',
                        'split_fastq': 'split_fastq.condor'}

        condor_entries = self.build_condor_arguments(result_map)
        for script_type in template_map.keys():
            template = loader.get_template(template_map[script_type])
            variables = {'python': sys.executable,
                         'logdir': self.log_path,
                         'env': os.environ.get('PYTHONPATH', None),
                         'args': condor_entries[script_type],
                         }

            context = Context(variables)

            with open(script_type + '.condor','w+') as outstream:
                outstream.write(template.render(context))

    def build_condor_arguments(self, result_map):
        condor_entries = {'srf': [],
                          'qseq': [],
                          'split_fastq': []}
        conversion_funcs = {'srf': self.condor_srf_to_fastq,
                            'qseq': self.condor_qseq_to_fastq,
                            'split_fastq': self.condor_desplit_fastq
                            }

        lib_db = self.find_archive_sequence_files(result_map)
        needed_targets = self.find_missing_targets(result_map, lib_db)

        for target_pathname, available_sources in needed_targets.items():
            LOGGER.debug(' target : %s' % (target_pathname,))
            LOGGER.debug(' candidate sources: %s' % (available_sources,))
            for condor_type in available_sources.keys():
                conversion = conversion_funcs.get(condor_type, None)
                if conversion is None:
                    errmsg = "Unrecognized type: {0} for {1}"
                    print errmsg.format(condor_type,
                                        pformat(available_sources))
                    continue
                sources = available_sources.get(condor_type, None)

                if sources is not None:
                    condor_entries.setdefault(condor_type, []).append(
                        conversion(sources, target_pathname))
            else:
                print " need file", target_pathname

        return condor_entries

    def find_archive_sequence_files(self,  result_map):
        """
        Find archived sequence files associated with our results.
        """
        LOGGER.debug("Searching for sequence files in: %s" %(self.sequences_path,))

        lib_db = {}
        seq_dirs = set()
        candidate_lanes = {}
        for lib_id in result_map.keys():
            lib_info = self.api.get_library(lib_id)
            lib_info['lanes'] = {}
            lib_db[lib_id] = lib_info

            for lane in lib_info['lane_set']:
                lane_key = (lane['flowcell'], lane['lane_number'])
                candidate_lanes[lane_key] = lib_id
                seq_dirs.add(os.path.join(self.sequences_path,
                                             'flowcells',
                                             lane['flowcell']))
        LOGGER.debug("Seq_dirs = %s" %(unicode(seq_dirs)))
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

    def find_missing_targets(self, result_map, lib_db):
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
        for lib_id in result_map.keys():
            result_dir = result_map[lib_id]
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
                        target_name = fastq_paired_template % \
                                      filename_attributes
                    else:
                        target_name = fastq_single_template % \
                                      filename_attributes

                    target_pathname = os.path.join(result_dir, target_name)
                    if self.force or not os.path.exists(target_pathname):
                        t = needed_targets.setdefault(target_pathname, {})
                        t.setdefault(seq.filetype, []).append(seq)

        return needed_targets


    def condor_srf_to_fastq(self, sources, target_pathname):
        if len(sources) > 1:
            raise ValueError("srf to fastq can only handle one file")

        return {
            'sources': [os.path.abspath(sources[0].path)],
            'pyscript': srf2fastq.__file__,
            'flowcell': sources[0].flowcell,
            'ispaired': sources[0].paired,
            'target': target_pathname,
            'target_right': target_pathname.replace('_r1.fastq', '_r2.fastq'),
            'mid': getattr(sources[0], 'mid_point', None),
            'force': self.force,
        }

    def condor_qseq_to_fastq(self, sources, target_pathname):
        paths = []
        for source in sources:
            paths.append(source.path)
        paths.sort()
        return {
            'pyscript': qseq2fastq.__file__,
            'flowcell': sources[0].flowcell,
            'target': target_pathname,
            'sources': paths,
            'ispaired': sources[0].paired,
            'istar': len(sources) == 1,
        }

    def condor_desplit_fastq(self, sources, target_pathname):
        paths = []
        for source in sources:
            paths.append(source.path)
        paths.sort()
        return {
            'pyscript': desplit_fastq.__file__,
            'target': target_pathname,
            'sources': paths,
            'ispaired': sources[0].paired,
        }

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

