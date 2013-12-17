import csv
import os
import re
from StringIO import StringIO

try:
    import json
except ImportError, e:
    import simplejson as json

from django.test import TestCase

from htsworkflow.frontend.auth import apidata
from htsworkflow.pipelines.retrieve_config import \
     format_gerald_config, \
     getCombinedOptions, \
     save_sample_sheet

class RetrieveTestCases(TestCase):
    fixtures = ['test_flowcells.json']

    def setUp(self):
        pass

    def test_format_gerald(self):
        flowcell_request = self.client.get('/experiments/config/FC12150/json', apidata)
        self.failUnlessEqual(flowcell_request.status_code, 200)
        flowcell_info = json.loads(flowcell_request.content)

        options = getCombinedOptions(['-f','FC12150','-g',os.getcwd()])
        genome_map = {u'Homo sapiens': '/tmp/hg18' }

        config = format_gerald_config(options, flowcell_info, genome_map)
        config_lines = config.split('\n')
        lane3 = [ line for line in config_lines if re.search('Lane3', line) ]
        self.failUnlessEqual(len(lane3), 1)
        self.failUnlessEqual(lane3[0], '# Lane3: SL039 | Paired ends 99 GM12892')
        human = [ line for line in config_lines if re.search('hg18', line) ]
        self.failUnlessEqual(len(human), 1)
        self.failUnlessEqual(human[0], '345678:ELAND_GENOME /tmp/hg18')
        # we changed the api to force unknown genomes to be sequencing
        sequencing = [ line for line in config_lines if re.search('sequence_pair', line) ]
        self.failUnlessEqual(len(sequencing), 2)


    def test_format_sample_sheet(self):
        fcid = '42JU1AAXX'
        url = '/experiments/config/%s/json' % (fcid,)
        flowcell_request = self.client.get(url, apidata)
        self.failUnlessEqual(flowcell_request.status_code, 200)
        flowcell_info = json.loads(flowcell_request.content)

        options = getCombinedOptions(['-f',fcid,'-g',os.getcwd(),])

        output = StringIO()
        save_sample_sheet(output, options, flowcell_info)

        output.seek(0)
        sheet = list(csv.DictReader(output))
        expected = [{'SampleProject': '12044_index1',
                     'Index': 'ATCACG',
                     'Lane': '3',
                     },
                    {'SampleProject': '12044_index2',
                     'Index': 'CGATGT',
                     'Lane': '3',
                     },
                    {'SampleProject': '12044_index3',
                     'Index': 'TTAGGC',
                     'Lane': '3',
                     },
                    {'SampleProject': '11045_index1',
                     'Index': 'ATCACG',
                     'Lane': '3',
                     },
                    {'SampleProject': '13044_indexN701-N501',
                     'Index': 'TAAGGCGA-TAGATCGC',
                     'Lane': '4',
                     }
                    ]
        self.failUnlessEqual(len(sheet), len(expected))
        for s, e in zip(sheet, expected):
            for key in e.keys():
                self.failUnlessEqual(s[key], e[key],
                  "%s != %s for key %s" % (s[key],e[key], key))
