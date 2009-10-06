import os
import re

try:
    import json
except ImportError, e:
    import simplejson as json
    
from django.test import TestCase

from htsworkflow.frontend.auth import apidata
from htsworkflow.pipelines.retrieve_config import format_gerald_config, getCombinedOptions

class RetrieveTestCases(TestCase):
    fixtures = ['test_flowcells.json']

    def setUp(self):
        pass

    def test_format_gerald(self):
        flowcell_request = self.client.get('/experiments/config/303TUAAXX/json', apidata)
        self.failUnlessEqual(flowcell_request.status_code, 200)

        print dir(flowcell_request)
        flowcell_info = json.loads(flowcell_request.content)

        options = getCombinedOptions(['-f','303TUAAXX','-g',os.getcwd()])        
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

                  

        
    
