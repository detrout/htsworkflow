import logging
import os

import RDF

from htsworkflow.submission.submission import Submission

from htsworkflow.util.rdfhelp import \
     fromTypedNode, \
     geoSoftNS, \
     simplifyUri, \
     submissionOntology

from django.conf import settings
from django.template import Context, loader

LOGGER = logging.getLogger(__name__)

class GEOSubmission(Submission):
    def __init__(self, name, model):
        super(GEOSubmission, self).__init__(name, model)

    def make_soft(self, result_map):
        samples = []
        platform = self.get_platform_metadata()
        platform_attribs = dict(platform)
        platform_id = platform_attribs['^platform']
        series = self.get_series_metadata()
        series_attribs = dict(series)
        series_id = series_attribs['^series']
        for lib_id, result_dir in result_map.items():
            an_analysis = self.get_submission_node(result_dir)
            metadata = self.get_sample_metadata(an_analysis)
            if len(metadata) > 1:
                errmsg = 'Confused there are more than one samples for %s'
                LOGGER.debug(errmsg % (str(an_analysis,)))
            metadata = metadata[0]
            metadata['raw'] = self.get_sample_files(an_analysis,
                                                    geoSoftNS['raw'])
            metadata['supplimental'] = self.get_sample_files(
                an_analysis,
                geoSoftNS['supplemental'])
            samples.append(metadata)

        soft_template = loader.get_template('geo_submission.soft')
        context = Context({
            'platform': platform,
            'series': series,
            'samples': samples,
            'platform_id': platform_id,
            'series_id': series_id,
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

    def get_platform_metadata(self):
        """Gather information for filling out sample section of a SOFT file
        """
        query_template = loader.get_template('geo_platform.sparql')
        submission = str(self.submissionSetNS[''].uri)
        context = Context({
            'submission': submission,
            })

        results = self.execute_query(query_template, context)
        return self.query_to_soft_dictionary(results, 'platform')

    def get_series_metadata(self):
        """Gather information for filling out sample section of a SOFT file
        """
        query_template = loader.get_template('geo_series.sparql')
        submission = str(self.submissionSetNS[''].uri)
        context = Context({
            'submission': submission,
            })

        results = self.execute_query(query_template, context)
        return self.query_to_soft_dictionary(results, 'series')

    def get_sample_metadata(self, analysis_node):
        """Gather information for filling out sample section of a SOFT file
        """
        query_template = loader.get_template('geo_samples.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'submissionSet': str(self.submissionSetNS[''].uri),
            })

        results = self.execute_query(query_template, context)
        for r in results:

            r['dataProtocol'] = str(r['dataProtocol']).replace('\n', ' ')
        return results

    def get_sample_files(self, analysis_node, file_class):
        """Gather files
        """
        query_template = loader.get_template('geo_files.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'file_class': str(file_class)
            })

        return self.execute_query(query_template, context)

    def query_to_soft_dictionary(self, results, heading):
        attributes = []
        for r in results:
            name = simplifyUri(geoSoftNS, r['name'])
            if name is not None:
                if name.lower() == heading.lower():
                    name = '^' + name
                else:
                    name = '!' + name
                for v in fromTypedNode(r['value']).split(os.linesep):
                    v = v.strip()
                    if len(v) > 0:
                        attributes.append((name, v))
        return attributes
