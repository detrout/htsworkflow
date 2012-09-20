"""Convert srf and qseq archive files to fastqs
"""
import logging
import os
from pprint import pformat,pprint
import sys
import types
from urlparse import urljoin, urlparse

from htsworkflow.pipelines.sequences import scan_for_sequences, \
     update_model_sequence_library
from htsworkflow.pipelines.samplekey import SampleKey
from htsworkflow.pipelines import qseq2fastq
from htsworkflow.pipelines import srf2fastq
from htsworkflow.pipelines import desplit_fastq
from htsworkflow.util.rdfhelp import get_model, dump_model, load_into_model, \
     fromTypedNode, \
     stripNamespace
from htsworkflow.util.rdfns import *
from htsworkflow.util.conversion import parse_flowcell_id

from django.conf import settings
from django.template import Context, loader

import RDF

LOGGER = logging.getLogger(__name__)


class CondorFastqExtract(object):
    def __init__(self, host, sequences_path,
                 log_path='log',
                 model=None,
                 force=False):
        """Extract fastqs from results archive

        Args:
          host (str): root of the htsworkflow api server
          apidata (dict): id & key to post to the server
          sequences_path (str): root of the directory tree to scan for files
          log_path (str): where to put condor log files
          force (bool): do we force overwriting current files?
        """
        self.host = host
        self.model = get_model(model)
        self.sequences_path = sequences_path
        self.log_path = log_path
        self.force = force
        LOGGER.info("CondorFastq host={0}".format(self.host))
        LOGGER.info("CondorFastq sequences_path={0}".format(self.sequences_path))
        LOGGER.info("CondorFastq log_path={0}".format(self.log_path))

    def create_scripts(self, result_map ):
        """
        Generate condor scripts to build any needed fastq files

        Args:
          result_map: htsworkflow.submission.results.ResultMap()
        """
        template_map = {'srf': 'srf.condor',
                        'qseq': 'qseq.condor',
                        'split_fastq': 'split_fastq.condor',
                        }

        env = None
        pythonpath = os.environ.get('PYTHONPATH', None)
        if pythonpath is not None:
            env = "PYTHONPATH=%s" % (pythonpath,)
        condor_entries = self.build_condor_arguments(result_map)
        for script_type in template_map.keys():
            template = loader.get_template(template_map[script_type])
            variables = {'python': sys.executable,
                         'logdir': self.log_path,
                         'env': env,
                         'args': condor_entries[script_type],
                         'root_url': self.host,
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
        sequences = self.find_archive_sequence_files(result_map)
        needed_targets = self.update_fastq_targets(result_map, sequences)

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
        self.import_libraries(result_map)
        flowcell_ids = self.find_relavant_flowcell_ids()
        self.import_sequences(flowcell_ids)

        query_text = """
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>

        select ?filenode ?filetype ?cycle ?lane_number ?read
               ?library  ?library_id
               ?flowcell ?flowcell_id ?read_length
               ?flowcell_type ?flowcell_status
        where {
            ?filenode libns:cycle ?cycle ;
                      libns:lane_number ?lane_number ;
                      libns:read ?read ;
                      libns:flowcell ?flowcell ;
                      libns:flowcell_id ?flowcell_id ;
                      libns:library ?library ;
                      libns:library_id ?library_id ;
                      libns:file_type ?filetype ;
                      a libns:illumina_result .
            ?flowcell libns:read_length ?read_length ;
                      libns:flowcell_type ?flowcell_type .
            OPTIONAL { ?flowcell libns:flowcell_status ?flowcell_status }
            FILTER(?filetype != libns:sequencer_result)
        }
        """
        LOGGER.debug("find_archive_sequence_files query: %s",
                     query_text)
        query = RDF.SPARQLQuery(query_text)
        results = []
        for r in query.execute(self.model):
            library_id = fromTypedNode(r['library_id'])
            if library_id in result_map:
                seq = SequenceResult(r)
                LOGGER.debug("Creating sequence result for library %s: %s",
                             library_id,
                             repr(seq))
                results.append(seq)
        return results

    def import_libraries(self, result_map):
        for lib_id in result_map.keys():
            lib_id_encoded = lib_id.encode('utf-8')
            liburl = urljoin(self.host, 'library/%s/' % (lib_id_encoded,))
            library = RDF.Node(RDF.Uri(liburl))
            self.import_library(library)

    def import_library(self, library):
        """Import library data into our model if we don't have it already
        """
        q = RDF.Statement(library, rdfNS['type'], libraryOntology['Library'])
        present = False
        if not self.model.contains_statement(q):
            present = True
            load_into_model(self.model, 'rdfa', library)
        LOGGER.debug("Did we import %s: %s", library, present)

    def find_relavant_flowcell_ids(self):
        """Generate set of flowcell ids that had samples of interest on them
        """
        flowcell_query =RDF.SPARQLQuery("""
prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

select distinct ?flowcell ?flowcell_id
WHERE {
  ?library a libns:Library ;
           libns:has_lane ?lane .
  ?lane libns:flowcell ?flowcell .
  ?flowcell libns:flowcell_id ?flowcell_id .
}""")
        flowcell_ids = set()
        for r in flowcell_query.execute(self.model):
            flowcell_ids.add( fromTypedNode(r['flowcell_id']) )
            LOGGER.debug("Flowcells = %s" %(unicode(flowcell_ids)))
            flowcell_test = RDF.Statement(r['flowcell'],
                                          rdfNS['type'],
                                          libraryOntology['IlluminaFlowcell'])
            if not self.model.contains_statement(flowcell_test):
                # we probably lack full information about the flowcell.
                load_into_model(self.model, 'rdfa', r['flowcell'])
        return flowcell_ids

    def import_sequences(self, flowcell_ids):
        seq_dirs = []
        for f in flowcell_ids:
            seq_dirs.append(os.path.join(self.sequences_path, str(f)))
        sequences = scan_for_sequences(seq_dirs)
        for seq in sequences:
            seq.save_to_model(self.model, self.host)
        update_model_sequence_library(self.model, self.host)

    def update_fastq_targets(self, result_map, raw_files):
        """Return list of fastq files that need to be built.

        Also update model with link between illumina result files
        and our target fastq file.
        """
        fastq_paired_template = '%(lib_id)s_%(flowcell)s_c%(cycle)s_l%(lane)s_r%(read)s.fastq'
        fastq_single_template = '%(lib_id)s_%(flowcell)s_c%(cycle)s_l%(lane)s.fastq'
        # find what targets we're missing
        needed_targets = {}
        for seq in raw_files:
            if not seq.isgood:
                continue
            filename_attributes = {
                'flowcell': seq.flowcell_id,
                'lib_id': seq.library_id,
                'lane': seq.lane_number,
                'read': seq.read,
                'cycle': seq.cycle
            }

            if seq.ispaired:
                target_name = fastq_paired_template % \
                              filename_attributes
            else:
                target_name = fastq_single_template % \
                              filename_attributes

            result_dir = result_map[seq.library_id]
            target_pathname = os.path.join(result_dir, target_name)
            if self.force or not os.path.exists(target_pathname):
                t = needed_targets.setdefault(target_pathname, {})
                t.setdefault(seq.filetype, []).append(seq)
            self.add_target_source_links(target_pathname, seq)
        return needed_targets

    def add_target_source_links(self, target, seq):
        """Add link between target pathname and the 'lane' that produced it
        (note lane objects are now post demultiplexing.)
        """
        target_uri = 'file://' + target.encode('utf-8')
        target_node = RDF.Node(RDF.Uri(target_uri))
        source_stmt = RDF.Statement(target_node, dcNS['source'], seq.filenode)
        self.model.add_statement(source_stmt)

    def condor_srf_to_fastq(self, sources, target_pathname):
        if len(sources) > 1:
            raise ValueError("srf to fastq can only handle one file")

        mid_point = None
        if sources[0].flowcell_id == '30DY0AAXX':
            mid_point = 76

        return {
            'sources': [sources[0].path],
            'pyscript': srf2fastq.__file__,
            'flowcell': sources[0].flowcell_id,
            'ispaired': sources[0].ispaired,
            'target': target_pathname,
            'target_right': target_pathname.replace('_r1.fastq', '_r2.fastq'),
            'mid': mid_point,
            'force': self.force,
        }

    def condor_qseq_to_fastq(self, sources, target_pathname):
        paths = []
        for source in sources:
            paths.append(source.path)
        paths.sort()
        return {
            'pyscript': qseq2fastq.__file__,
            'flowcell': sources[0].flowcell_id,
            'target': target_pathname,
            'sources': paths,
            'ispaired': sources[0].ispaired,
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
            'ispaired': sources[0].ispaired,
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

class SequenceResult(object):
    """Convert the sparql query result from find_archive_sequence_files
    """
    def __init__(self, result):
        self.filenode = result['filenode']
        self._filetype = result['filetype']
        self.cycle = fromTypedNode(result['cycle'])
        self.lane_number = fromTypedNode(result['lane_number'])
        self.read = fromTypedNode(result['read'])
        if type(self.read) in types.StringTypes:
            self.read = 1
        self.library = result['library']
        self.library_id = fromTypedNode(result['library_id'])
        self.flowcell = result['flowcell']
        self.flowcell_id = fromTypedNode(result['flowcell_id'])
        self.flowcell_type = fromTypedNode(result['flowcell_type'])
        self.flowcell_status = fromTypedNode(result['flowcell_status'])

    def _is_good(self):
        """is this sequence / flowcell 'good enough'"""
        if self.flowcell_status is not None and \
           self.flowcell_status.lower() == "failed":
            return False
        return True
    isgood = property(_is_good)

    def _get_ispaired(self):
        if self.flowcell_type.lower() == "paired":
            return True
        else:
            return False
    ispaired = property(_get_ispaired)

    def _get_filetype(self):
        return stripNamespace(libraryOntology, self._filetype)
    filetype = property(_get_filetype)

    def _get_path(self):
        url = urlparse(str(self.filenode.uri))
        if url.scheme == 'file':
            return url.path
        else:
            errmsg = u"Unsupported scheme {0} for {1}"
            raise ValueError(errmsg.format(url.scheme, unicode(url)))
    path = property(_get_path)

    def __repr__(self):
        return "SequenceResult({0},{1},{2})".format(
            str(self.filenode),
            str(self.library_id),
            str(self.flowcell_id))
