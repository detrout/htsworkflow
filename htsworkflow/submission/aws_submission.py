"""Partially through ENCODE3 the DCC switched to needing to upload via AWS
"""

import logging
import json
import os
from pprint import pformat, pprint
import subprocess
import time

from requests.exceptions import HTTPError

from htsworkflow.submission.submission import Submission
from .encoded import ENCODED

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

        self._replicates = {}
        self._files = {}


    def check_upload(self, results_map):
        tocheck = []
        # phase one download data
        for an_analysis in self.analysis_nodes(results_map):
            for metadata in self.get_metadata(an_analysis):
                filename = self.make_upload_filename(metadata)
                if os.path.exists(filename):
                    with open(filename, 'rt') as instream:
                        uploaded = json.load(instream)
                    tocheck.append({
                        'submitted_file_name': uploaded['submitted_file_name'],
                        'md5sum': uploaded['md5sum']
                    })
                    self.update_replicates(uploaded)

        # phase 2 make sure submitted file is there
        md5sums = set((self._files[f]['md5sum'] for f in self._files))
        submitted_file_names = set(
            (self._files[f]['submitted_file_name'] for f in self._files)
        )
        errors_detected = 0
        for row in tocheck:
            error = []
            if row['submitted_file_name'] not in submitted_file_names:
                error.append('!file_name')
            if row['md5sum'] not in md5sums:
                error.append('!md5sum')
            if error:
                print("{} failed {} checks".format(
                    row['submitted_file_name'],
                    ', '.join(error)
                ))
                errors_detected += 1

        if not errors_detected:
            print('No errors detected')

    def update_replicates(self, metadata):
        replicate_id = metadata['replicate']
        if replicate_id not in self._replicates:
            LOGGER.debug("Downloading %s", replicate_id)
            try:
                rep = self.encode.get_json(replicate_id)

                self._replicates[replicate_id] = rep
                for file_id in rep['experiment']['files']:
                    self.update_files(file_id)
            except HTTPError as err:
                print(err.response, dir(err.response))
                if err.response.status_code == 404:
                    print('Unable to find {} {}'.format(
                        replicate_id,
                        metadata['submitted_file_name'])
                    )
                else:
                    raise err

    def update_files(self, file_id):
        if file_id not in self._files:
            LOGGER.debug("Downloading %s", file_id)
            try:
                file_object = self.encode.get_json(file_id)
                self._files[file_id] = file_object
            except HTTPError as err:
                if err.response.status_code == 404:
                    print('unable to find {}'.format(file_id))
                else:
                    raise err

    def upload(self, results_map, dry_run=False):
        for an_analysis in self.analysis_nodes(results_map):
            for metadata in self.get_metadata(an_analysis):
                metadata['@type'] = ['file']
                self.encode.validate(metadata)
                del metadata['@type']

                if dry_run:
                    LOGGER.info(json.dumps(metadata, indent=4, sort_keys=True))
                    continue

                upload = self.make_upload_filename(metadata)
                if not os.path.exists(upload):
                    with open(upload, 'w') as outstream:
                        json.dump(metadata, outstream, indent=4, sort_keys=True)
                    LOGGER.debug(json.dumps(metadata, indent=4, sort_keys=True))

                    response = self.encode.post_json('/file', metadata)
                    LOGGER.info(json.dumps(response, indent=4, sort_keys=True))

                    item = response['@graph'][0]
                    creds = item['upload_credentials']
                    run_aws_cp(metadata['submitted_file_name'], creds)
                else:
                    LOGGER.info('%s already uploaded',
                                metadata['submitted_file_name'])


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
            if 'read_length' in row:
                row['read_length'] = int(row['read_length'])
            flowcell_details = {}
            for term in ['machine', 'flowcell', 'lane', 'barcode']:
                if term in row:
                    value = str(row[term])
                    flowcell_details[term] = value
                    del row[term]
            if len(flowcell_details) > 0:
                row['flowcell_details'] = [flowcell_details]

        return results

    def make_upload_filename(self, metadata):
        return metadata['submitted_file_name'] + '.upload'

def run_aws_cp(pathname, creds):
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
