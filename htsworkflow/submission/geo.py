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
            if len(metadata) == 0:
                errmsg = 'No metadata found for {0}'
                LOGGER.error(errmsg.format(str(an_analysis),))
                continue
            elif len(metadata) > 1:
                errmsg = 'Confused there are more than one samples for %s'
                LOGGER.debug(errmsg % (str(an_analysis),))
            metadata = metadata[0]
            metadata['raw'] = self.get_raw_files(an_analysis)
            metadata['supplimental'] = self.get_sample_files(an_analysis)
            metadata['run'] = self.get_run_details(an_analysis)
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

    def get_sample_files(self, analysis_node):
        """Gather derived files
        """
        query_template = loader.get_template('geo_files.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'file_class': str(geoSoftNS['supplemental'])
            })

        return self.execute_query(query_template, context)

    def get_raw_files(self, analysis_node):
        """Gather raw data e.g. fastq files.
        """
        query_template = loader.get_template('geo_fastqs.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'file_class': str(geoSoftNS['raw']),
            })

        lanes = {}
        for row in self.execute_query(query_template, context):
            data = {}
            for k, v in row.items():
                data[k] = v
            lane = str(data['lane'])
            lanes.setdefault(lane, []).append(data)
        result = []
        for lane, files in lanes.items():
            if len(files) > 2:
                errmsg = "Don't know what to do with more than 2 raw files"
                raise ValueError(errmsg)
            elif len(files) == 2:
                is_paired = True
            elif len(files) == 1:
                is_paired = False
            elif len(files) == 0:
                raise RuntimeError("Empty lane list discovered")
            files = self._format_filename(files, is_paired)
            files = self._format_flowcell_type(files, is_paired)
            files = self._format_read_length(files, is_paired)
            result.append(files[0])
        return result

    def _format_flowcell_type(self, files, is_paired):
        """Used by get_raw_files to format value for single_or_paired-end
        """
        for f in files:
            if 'flowcell_type' in f:
                flowcell_type = fromTypedNode(f['flowcell_type'])
                if flowcell_type is None:
                    pass
                elif flowcell_type.lower() == "paired":
                    f['flowcell_type'] = 'paired-end'
                else:
                    f['flowcell_type'] = 'single'

        return files

    def _format_read_length(self, files, is_paired):
        """Format
        """
        read_count = 2 if is_paired else 1
        for f in files:
            if 'read_length' in f:
                read_length = str(fromTypedNode(f['read_length']))
                f['read_length'] = ",".join([read_length] * read_count)
        return files

    def _format_filename(self, files, is_paired):
        """Format file name for get_raw_files, also report if paired
        """
        if len(files) == 2:
            # should be paired
            f0 = files[0]
            f1 = files[1]
            f0['filename'] = "%s, %s" % (str(f0['filename']),
                                         str(f1['filename']))
            f0['md5sum'] = "%s, %s" % (str(f0['md5sum']),
                                       str(f1['md5sum']))
            del files[1]
        else:
            files[0]['filename'] = str(files[0]['filename'])
            files[0]['md5sum'] = str(files[0]['md5sum'])
        return files


    def get_run_details(self, analysis_node):
        """Get information about runs
        """
        query_template = loader.get_template('geo_run_details.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            })

        return self.execute_query(query_template, context)

    def query_to_soft_dictionary(self, results, heading):
        attributes = []
        for r in results:
            name = stripNamespace(geoSoftNS, r['name'])
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
