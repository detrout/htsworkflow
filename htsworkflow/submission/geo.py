import logging

import RDF

from htsworkflow.submission.submission import Submission

from htsworkflow.util.rdfhelp import \
     fromTypedNode, \
     submissionOntology

from django.conf import settings
from django.template import Context, loader

LOGGER = logging.getLogger(__name__)

class GEOSubmission(Submission):
    def __init__(self, name, model):
        super(GEOSubmission, self).__init__(name, model)

    def make_soft(self, result_map):
        samples = []
        for lib_id, result_dir in result_map.items():
            an_analysis = self.get_submission_node(result_dir)
            samples.append(self.get_sample_metadata(an_analysis))

        soft_template = loader.get_template('geo_submission.soft')
        context = Context({
            'samples': samples
        })
        print str(soft_template.render(context))

    def check_for_name(self, analysis_node):
        name = fromTypedNode(
            self.model.get_target(analysis_node,
                                  submissionOntology['name']))
        if name is None:
            logger.error("Need name for %s" % (str(analysis_node)))
            return False
        else:
            return True

    def get_sample_metadata(self, analysis_node):
        """Gather information for filling out sample section of a SOFT file
        """
        query_template = loader.get_template('geo_submission.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            })

        formatted_query = query_template.render(context)
        query = RDF.SPARQLQuery(str(formatted_query))
        rdfstream = query.execute(self.model)
        results = []
        for r in rdfstream:
            results.append(r)
        return results
