#!/usr/bin/env python

import copy
import os
from pprint import pprint
import shutil
import tempfile
import unittest

from htsworkflow.submission import condorfastq

FCDIRS = [
    'C02F9ACXX',
    'C02F9ACXX/C1-202',
    'C02F9ACXX/C1-202/Project_11154',
    'C02F9ACXX/C1-202/Project_12342_Index1',
    'C02F9ACXX/C1-202/Project_12342_Index2',
    '42JUYAAXX',
    '42JUYAAXX/C1-76',
    '30221AAXX',
    '30221AAXX/C1-33',
    '61MJTAAXX',
    '61MJTAAXX/C1-76',
]

DATAFILES = [
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R1_002.fastq.gz',
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R2_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R2_002.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index1/11114_GCCAAT_L004_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index2/11119_CGATGT_L007_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index2/11119_CGATGT_L005_R1_001.fastq.gz',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l1_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l2_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l3_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l4_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l6_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l7_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l8_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l1_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l1_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l2_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l3_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l4_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l6_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l7_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l8_r2.tar.bz2',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_1.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_2.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_3.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_4.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_5.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_6.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_7.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_8.srf',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l1_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l2_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l3_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l4_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l5_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l6_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l7_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l8_r1.tar.bz2',
]

LIBDATA = {
    '11154':{u'antibody_id': None,
             u'cell_line': u'Unknown',
             u'cell_line_id': 1,
             u'experiment_type': u'RNA-seq',
             u'experiment_type_id': 4,
             u'gel_cut_size': 300,
             u'hidden': False,
             u'id': u'11154',
             u'insert_size': 200,
             u'lane_set': [{u'flowcell': u'30221AAXX',
                            u'lane_number': 4,
                            u'paired_end': False,
                            u'read_length': 33,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'42JUYAAXX',
                            u'lane_number': 5,
                            u'paired_end': True,
                            u'read_length': 76,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'61MJTAAXX',
                            u'lane_number': 6,
                            u'paired_end': False,
                            u'read_length': 76,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'C02F9ACXX',
                            u'lane_number': 3,
                            u'paired_end': True,
                            u'read_length': 101,
                            u'status': u'Unknown',
                            u'status_code': None}],
             u'library_id': u'11154',
             u'library_name': u'Paired ends ASDF ',
             u'library_species': u'Mus musculus',
             u'library_species_id': 9,
             u'library_type': u'Paired End (non-multiplexed)',
             u'library_type_id': 2,
             u'made_by': u'Gary Gygax',
             u'made_for': u'TSR',
             u'notes': u'300 bp gel fragment',
             u'replicate': 1,
             u'stopping_point': u'1Aa',
             u'successful_pM': None,
             u'undiluted_concentration': u'29.7'}
    }

FAKE_APIDATA = {'apiid':0, 'apikey': 'foo'}

class FakeApi(object):
    def __init__(self, *args, **kwargs):
        pass

    def get_library(self, libid):
        lib_data = LIBDATA[libid]
        return copy.deepcopy(lib_data)

class TestCondorFastq(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='condorfastq_test')
        self.flowcelldir = os.path.join(self.tempdir, 'flowcells')
        os.mkdir(self.flowcelldir)

        self.logdir = os.path.join(self.tempdir, 'log')
        os.mkdir(self.logdir)

        for d in FCDIRS:
            os.mkdir(os.path.join(self.flowcelldir, d))

        for f in DATAFILES:
            filename = os.path.join(self.flowcelldir, f)
            with open(filename, 'w') as stream:
                stream.write('testfile')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_find_archive_sequence(self):
        extract = condorfastq.CondorFastqExtract('host',
                                                 FAKE_APIDATA,
                                                 self.tempdir,
                                                 self.logdir)
        extract.api = FakeApi()
        result_map = [('11154', '/notarealplace')]
        lib_db = extract.find_archive_sequence_files(result_map)

        self.failUnlessEqual(len(lib_db['11154']['lanes']), 4)
        lanes = [
            lib_db['11154']['lanes'][(u'30221AAXX', 4)],
            lib_db['11154']['lanes'][(u'42JUYAAXX', 5)],
            lib_db['11154']['lanes'][(u'61MJTAAXX', 6)],
            lib_db['11154']['lanes'][(u'C02F9ACXX', 3)],
        ]
        self.failUnlessEqual(len(lanes[0]), 1)
        self.failUnlessEqual(len(lanes[1]), 2)
        self.failUnlessEqual(len(lanes[2]), 1)
        self.failUnlessEqual(len(lanes[3]), 4)

    def test_find_needed_targets(self):

        extract = condorfastq.CondorFastqExtract('host',
                                                 FAKE_APIDATA,
                                                 self.tempdir,
                                                 self.logdir)
        extract.api = FakeApi()
        result_map = [('11154', '/notarealplace')]
        lib_db = extract.find_archive_sequence_files(result_map)

        needed_targets = extract.find_missing_targets(result_map,
                                                      lib_db)
        self.failUnlessEqual(len(needed_targets), 6)
        srf_30221 = needed_targets[
            u'/notarealplace/11154_30221AAXX_c33_l4.fastq']
        qseq_42JUY_r1 = needed_targets[
            u'/notarealplace/11154_42JUYAAXX_c76_l5_r1.fastq']
        qseq_42JUY_r2 = needed_targets[
            u'/notarealplace/11154_42JUYAAXX_c76_l5_r2.fastq']
        qseq_61MJT = needed_targets[
            u'/notarealplace/11154_61MJTAAXX_c76_l6.fastq']
        split_C02F9_r1 = needed_targets[
            u'/notarealplace/11154_C02F9ACXX_c202_l3_r1.fastq']
        split_C02F9_r2 = needed_targets[
            u'/notarealplace/11154_C02F9ACXX_c202_l3_r2.fastq']

        self.failUnlessEqual(len(srf_30221['srf']), 1)
        self.failUnlessEqual(len(qseq_42JUY_r1['qseq']), 1)
        self.failUnlessEqual(len(qseq_42JUY_r2['qseq']), 1)
        self.failUnlessEqual(len(qseq_61MJT['qseq']), 1)
        self.failUnlessEqual(len(split_C02F9_r1['split_fastq']), 2)
        self.failUnlessEqual(len(split_C02F9_r2['split_fastq']), 2)

        #print '-------needed targets---------'
        #pprint(needed_targets)

    def test_generate_fastqs(self):
        extract = condorfastq.CondorFastqExtract('host',
                                                 FAKE_APIDATA,
                                                 self.tempdir,
                                                 self.logdir)
        extract.api = FakeApi()
        result_map = [('11154', '/notarealplace')]
        commands = extract.build_condor_arguments(result_map)

        srf = commands['srf']
        qseq = commands['qseq']
        split = commands['split_fastq']

        self.failUnlessEqual(len(srf), 1)
        self.failUnlessEqual(len(qseq), 3)
        self.failUnlessEqual(len(split), 2)

        srf_data = {u'/notarealplace/11154_30221AAXX_c33_l4.fastq':
                     [u'30221AAXX',
                      u'woldlab_090425_HWI-EAS229_0110_30221AAXX_4.srf'],
                     }
        for args in srf:
            args = extract_argument_list(args)
            expected = srf_data[args[3]]
            self.failUnless(expected[0] in args[5])
            self.failUnless(expected[1] in args[0])

        qseq_data = {u'/notarealplace/11154_42JUYAAXX_c76_l5_r1.fastq':
                     [u'42JUYAAXX',
                      u'woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r1.tar.bz2'],
                     u'/notarealplace/11154_61MJTAAXX_c76_l6.fastq':
                     ['61MJTAAXX',
                      'woldlab_100826_HSI-123_0001_61MJTAAXX_l6_r1.tar.bz2'],
                     u'/notarealplace/11154_42JUYAAXX_c76_l5_r2.fastq':
                     ['42JUYAAXX',
                      'woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2'],
                     }
        for args in qseq:
            args = extract_argument_list(args)
            expected = qseq_data[args[1]]
            self.failUnless(expected[0] in args[3])
            self.failUnless(expected[1] in args[5])

        split_data ={u'/notarealplace/11154_C02F9ACXX_c202_l3_r2.fastq':
                     [u'11154_NoIndex_L003_R2_001.fastq.gz',
                      u'11154_NoIndex_L003_R2_002.fastq.gz'],
                     u'/notarealplace/11154_C02F9ACXX_c202_l3_r1.fastq':
                     [u'11154_NoIndex_L003_R1_001.fastq.gz',
                      u'11154_NoIndex_L003_R1_002.fastq.gz'],
                     }
        for args in split:
            args = extract_argument_list(args)
            expected = split_data[args[1]]
            self.failUnless(expected[0] in args[2])
            self.failUnless(expected[1] in args[3])

        #print '-------commands---------'
        #pprint (commands)

def extract_argument_list(condor_argument):
    args = condor_argument.split()
    # eat the command name, and the trailing queue
    return args[1:-1]

def suite():
    suite = unittest.makeSuite(TestCondorFastq, 'test')
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')

