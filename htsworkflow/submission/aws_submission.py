"""Partially through ENCODE3 the DCC switched to needing to upload via AWS
"""

import logging
import json
import os
from pprint import pformat, pprint
import string
import subprocess
import time
import re

import jsonschema
import RDF

from htsworkflow.submission.submission import Submission
from .encoded import ENCODED
from htsworkflow.util.rdfhelp import \
     fromTypedNode, \
     geoSoftNS, \
     submissionOntology
from htsworkflow.util.ucsc import bigWigInfo

from django.conf import settings
from django.template import Context, loader

LOGGER = logging.getLogger(__name__)

class AWSSubmission(Submission):
    def __init__(self, name, model, encode_host, lims_host):
        """Create a AWS based submission

        :Parameters:
          - `name`: Name of submission
          - `model`: librdf model reference
          - `host`: hostname for library pages.
        """
        super(AWSSubmission, self).__init__(name, model, lims_host)
        self.encode = ENCODED(encode_host)
        self.encode.load_netrc()

    def upload(self, results_map, dry_run=False):
        for an_analysis in self.analysis_nodes(results_map):
            for metadata in self.get_metadata(an_analysis):
                metadata['@type'] = ['file']
                self.encode.validate(metadata)
                del metadata['@type']

                if dry_run:
                    LOGGER.info(json.dumps(metadata, indent=4, sort_keys=True))
                    continue

                upload = metadata['submitted_file_name'] + '.upload'
                if not os.path.exists(upload):
                    with open(upload, 'w') as outstream:
                        outstream.write(json.dumps(metadata, indent=4, sort_keys=True))
                    LOGGER.debug(json.dumps(metadata, indent=4, sort_keys=True))

                    response = self.encode.post_json('/file', metadata)
                    LOGGER.info(json.dumps(response, indent=4, sort_keys=True))

                    item = response['@graph'][0]
                    creds = item['upload_credentials']
                    self.run_aws_cp(metadata['submitted_file_name'], creds)
                else:
                    LOGGER.info('%s already uploaded',
                                metadata['submitted_file_name'])


    def run_aws_cp(self, pathname, creds):
        env = os.environ.copy()
        env.update({
            'AWS_ACCESS_KEY_ID': creds['access_key'],
            'AWS_SECRET_ACCESS_KEY': creds['secret_key'],
            'AWS_SECURITY_TOKEN': creds['session_token'],
        })
        start = time.time()
        try:
            subprocess.check_call(['aws', 's3', 'cp', pathname, creds['upload_url']], env=env)
        except subprocess.CalledProcessError as e:
            LOGGER.error('Upload of %s failed with exit code %d', pathname, e.returncode)
            return
        else:
            end = time.time()
            LOGGER.info('Upload of %s finished in %.2f seconds',
                        pathname,
                        end-start)


    def get_metadata(self, analysis_node):
        # convert our model names to encode project aliases
        platform_alias = {
            'Illumina HiSeq 2500': 'ENCODE:HiSeq2500'
        }
        query_template = loader.get_template('aws_metadata.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'submissionSet': str(self.submissionSetNS[''].uri),
            })
        results = self.execute_query(query_template, context)
        LOGGER.info("scanned %s for results found %s",
                    str(analysis_node), len(results))

        # need to adjust the results of the query slightly.
        for row in results:
            if 'platform' in row:
                row['platform'] = platform_alias[row['platform']]
            flowcell_details = {}
            for term in ['machine', 'flowcell', 'lane', 'barcode']:
                if term in row:
                    value = str(row[term])
                    flowcell_details[term] = value
                    del row[term]
            if len(flowcell_details) > 0:
                row['flowcell_details'] = [flowcell_details]

        return results
