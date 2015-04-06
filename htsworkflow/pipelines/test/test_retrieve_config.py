import csv
import os
import re
from six.moves import StringIO

import json

from django.test import TestCase
from django.utils.encoding import smart_text

from samples.samples_factory import LibraryFactory, LibraryTypeFactory, \
    MultiplexIndexFactory
from experiments.experiments_factory import FlowCellFactory, LaneFactory

from htsworkflow.auth import apidata
from htsworkflow.pipelines.retrieve_config import \
     format_gerald_config, \
     getCombinedOptions, \
     save_sample_sheet, \
     format_project_name

class RetrieveTestCases(TestCase):
    def setUp(self):
        pass

    def test_format_gerald(self):
        fc = FlowCellFactory.create(flowcell_id='FC12150')
        library = LibraryFactory.create()
        lane = LaneFactory(flowcell=fc, library=library, lane_number=3)

        flowcell_request = self.client.get('/experiments/config/FC12150/json',
                                           apidata)
        self.failUnlessEqual(flowcell_request.status_code, 200)
        flowcell_info = json.loads(smart_text(flowcell_request.content))['result']

        options = getCombinedOptions(['-f','FC12150','-g',os.getcwd()])
        genome_map = {library.library_species.scientific_name: '/tmp/build' }

        config = format_gerald_config(options, flowcell_info, genome_map)
        config_lines = config.split('\n')
        lane3 = [ line for line in config_lines if re.search('Lane3', line) ]
        self.failUnlessEqual(len(lane3), 1)
        expected = '# Lane3: {} | {}'.format(library.id, library.library_name)
        self.failUnlessEqual(lane3[0], expected)
        human = [ line for line in config_lines if re.search('build', line) ]
        self.failUnlessEqual(len(human), 1)
        self.failUnlessEqual(human[0], '3:ELAND_GENOME /tmp/build')


    def test_format_sample_sheet(self):
        fcid = '42JU1AAXX'
        fc = FlowCellFactory.create(flowcell_id=fcid)
        library_type = LibraryTypeFactory(can_multiplex=True)
        multiplex_index1 = MultiplexIndexFactory(adapter_type=library_type)
        multiplex_index2 = MultiplexIndexFactory(adapter_type=library_type)

        library1 = LibraryFactory.create(
            library_type=library_type,
            multiplex_id=multiplex_index1.multiplex_id)
        library2 = LibraryFactory.create(
            library_type=library_type,
            multiplex_id=multiplex_index2.multiplex_id)

        lane1l1 = LaneFactory(flowcell=fc, library=library1, lane_number=1)
        lane1l2 = LaneFactory(flowcell=fc, library=library2, lane_number=1)
        lane2l1 = LaneFactory(flowcell=fc, library=library1, lane_number=2)
        lane2l2 = LaneFactory(flowcell=fc, library=library2, lane_number=2)

        url = '/experiments/config/%s/json' % (fcid,)
        flowcell_request = self.client.get(url, apidata)
        self.failUnlessEqual(flowcell_request.status_code, 200)
        flowcell_info = json.loads(smart_text(flowcell_request.content))['result']

        options = getCombinedOptions(['-f',fcid,'-g',os.getcwd(),])

        output = StringIO()
        save_sample_sheet(output, options, flowcell_info)

        output.seek(0)
        sheet = list(csv.DictReader(output))
        name1 = library1.id + '_index' + next(iter(library1.index_sequences()))
        name2 = library2.id + '_index' + next(iter(library2.index_sequences()))
        expected = [{'SampleProject': name1,
                     'Index': next(iter(library1.index_sequences().values())),
                     'Lane': '1',
                     },
                    {'SampleProject': name2,
                     'Index': next(iter(library2.index_sequences().values())),
                     'Lane': '1',
                     },
                    {'SampleProject': name1,
                     'Index': next(iter(library1.index_sequences().values())),
                     'Lane': '2',
                     },
                    {'SampleProject': name2,
                     'Index': next(iter(library2.index_sequences().values())),
                     'Lane': '2',
                     },
                    ]
        self.failUnlessEqual(len(sheet), len(expected))
        for s, e in zip(sheet, expected):
            for key in e.keys():
                self.failUnlessEqual(s[key], e[key],
                  "%s != %s for key %s" % (s[key],e[key], key))
