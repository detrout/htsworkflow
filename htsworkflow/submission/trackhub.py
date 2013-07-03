import logging
import os

import RDF

from htsworkflow.submission.submission import Submission

from htsworkflow.util.rdfhelp import \
     fromTypedNode, \
     geoSoftNS, \
     stripNamespace, \
     submissionOntology

from django.conf import settings
from django.template import Context, loader

LOGGER = logging.getLogger(__name__)

class TrackHubSubmission(Submission):
    def __init__(self, name, model, host):
        super(TrackHubSubmission, self).__init__(name, model, host)

    def make_hub(self, result_map):
        samples = []
        for lib_id, result_dir in result_map.items():
            an_analysis = self.get_submission_node(result_dir)
            metadata = self.get_sample_metadata(an_analysis)
            if len(metadata) == 0:
                errmsg = 'No metadata found for {0}'
                LOGGER.error(errmsg.format(str(an_analysis),))
                continue
            elif len(metadata) > 1:
                errmsg = 'Confused there are more than one sample for %s'
                LOGGER.debug(errmsg % (str(an_analysis),))
            metadata = metadata[0]
            samples.append(metadata)

        template = loader.get_template('trackDb.txt')
        context = Context({
            'samples': samples,
        })
        return str(template.render(context))

    def make_manifest(self, result_map):
        files = []
        for lib_id, result_dir in result_map.items():
            an_analysis = self.get_submission_node(result_dir)
            metadata = self.get_manifest_metadata(an_analysis)
            files.extend(metadata)

        template = loader.get_template('manifest.txt')
        context = Context({
            'files': files
        })
        return str(template.render(context))
        
    def get_sample_metadata(self, analysis_node):
        """Gather information for filling out sample section of a SOFT file
        """
        query_template = loader.get_template('trackhub_samples.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'submissionSet': str(self.submissionSetNS[''].uri),
            })

        results = self.execute_query(query_template, context)
        return results

    def get_manifest_metadata(self, analysis_node):
        query_template = loader.get_template('trackhub_manifest.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'submissionSet': str(self.submissionSetNS[''].uri),
            })
        results = self.execute_query(query_template, context)
        return results
