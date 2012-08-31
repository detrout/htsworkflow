#!/usr/bin/env python

import copy
import os
from pprint import pprint
import shutil
import tempfile
import unittest

from htsworkflow.submission import condorfastq
from htsworkflow.submission.results import ResultMap

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
    '30DY0AAXX',
    '30DY0AAXX/C1-151',
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
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_1.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_2.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_3.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_4.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_5.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_6.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_7.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_8.srf',
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
                            u'lane_id': 3400,
                            u'paired_end': False,
                            u'read_length': 33,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'42JUYAAXX',
                            u'lane_number': 5,
                            u'lane_id': 4200,
                            u'paired_end': True,
                            u'read_length': 76,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'61MJTAAXX',
                            u'lane_number': 6,
                            u'lane_id': 6600,
                            u'paired_end': False,
                            u'read_length': 76,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'30DY0AAXX',
                            u'lane_number': 8,
                            u'lane_id': 3800,
                            u'paired_end': True,
                            u'read_length': 76,
                            u'status': u'Unknown',
                            u'status_code': None},
                           {u'flowcell': u'C02F9ACXX',
                            u'lane_number': 3,
                            u'lane_id': 12300,
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
        self.root_url = 'http://localhost'

    def get_library(self, libid):
        lib_data = LIBDATA[libid]
        return copy.deepcopy(lib_data)



class TestCondorFastq(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()

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

        self.subname = unicode('sub-11154')
        self.subdir = os.path.join(self.tempdir, self.subname)
        os.mkdir(self.subdir)

        self.result_map = ResultMap()
        self.result_map['11154'] = self.subname

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        os.chdir(self.cwd)

    def test_find_archive_sequence(self):
        extract = condorfastq.CondorFastqExtract('host',
                                                 FAKE_APIDATA,
                                                 self.tempdir,
                                                 self.logdir)
        extract.api = FakeApi()

        lib_db = extract.find_archive_sequence_files(self.result_map)

        self.failUnlessEqual(len(lib_db['11154']['lanes']), 5)
        lanes = [
            lib_db['11154']['lanes'][(u'30221AAXX', 4)],
            lib_db['11154']['lanes'][(u'42JUYAAXX', 5)],
            lib_db['11154']['lanes'][(u'61MJTAAXX', 6)],
            lib_db['11154']['lanes'][(u'30DY0AAXX', 8)],
            lib_db['11154']['lanes'][(u'C02F9ACXX', 3)],
        ]
        self.failUnlessEqual(len(lanes[0]), 1)
        self.failUnlessEqual(len(lanes[1]), 2)
        self.failUnlessEqual(len(lanes[2]), 1)
        self.failUnlessEqual(len(lanes[3]), 1)
        self.failUnlessEqual(len(lanes[4]), 4)

    def test_find_needed_targets(self):

        extract = condorfastq.CondorFastqExtract('host',
                                                 FAKE_APIDATA,
                                                 self.tempdir,
                                                 self.logdir)
        extract.api = FakeApi()
        lib_db = extract.find_archive_sequence_files(self.result_map)

        needed_targets = extract.find_missing_targets(self.result_map,
                                                      lib_db)
        self.failUnlessEqual(len(needed_targets), 7)
        srf_30221 = needed_targets[
            self.subname + u'/11154_30221AAXX_c33_l4.fastq']
        qseq_42JUY_r1 = needed_targets[
            self.subname + u'/11154_42JUYAAXX_c76_l5_r1.fastq']
        qseq_42JUY_r2 = needed_targets[
            self.subname + u'/11154_42JUYAAXX_c76_l5_r2.fastq']
        qseq_61MJT = needed_targets[
            self.subname + u'/11154_61MJTAAXX_c76_l6.fastq']
        split_C02F9_r1 = needed_targets[
            self.subname + u'/11154_C02F9ACXX_c202_l3_r1.fastq']
        split_C02F9_r2 = needed_targets[
            self.subname + u'/11154_C02F9ACXX_c202_l3_r2.fastq']

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
        commands = extract.build_condor_arguments(self.result_map)

        srf = commands['srf']
        qseq = commands['qseq']
        split = commands['split_fastq']

        self.failUnlessEqual(len(srf), 2)
        self.failUnlessEqual(len(qseq), 3)
        self.failUnlessEqual(len(split), 2)

        srf_data = {
            os.path.join(self.subname, '11154_30221AAXX_c33_l4.fastq'): {
                'mid': None,
                'ispaired': False,
                'sources': [u'woldlab_090425_HWI-EAS229_0110_30221AAXX_4.srf'],
                'flowcell': u'30221AAXX',
                'target': os.path.join(self.subname,
                                       u'11154_30221AAXX_c33_l4.fastq'),
            },
            os.path.join(self.subname, '11154_30DY0AAXX_c151_l8_r1.fastq'): {
                'mid': None,
                'ispaired': True,
                'flowcell': u'30DY0AAXX',
                'sources': [u'woldlab_090725_HWI-EAS229_0110_30DY0AAXX_8.srf'],
                'mid': 76,
                'target':
                    os.path.join(self.subname,
                                 u'11154_30DY0AAXX_c151_l8_r1.fastq'),
                'target_right':
                    os.path.join(self.subname,
                                 u'11154_30DY0AAXX_c151_l8_r2.fastq'),
            }
        }
        for args in srf:
            expected = srf_data[args['target']]
            self.failUnlessEqual(args['ispaired'], expected['ispaired'])
            self.failUnlessEqual(len(args['sources']), 1)
            _, source_filename = os.path.split(args['sources'][0])
            self.failUnlessEqual(source_filename, expected['sources'][0])
            self.failUnlessEqual(args['target'], expected['target'])
            if args['ispaired']:
                self.failUnlessEqual(args['target_right'],
                                     expected['target_right'])
            if 'mid' in expected:
                self.failUnlessEqual(args['mid'], expected['mid'])

        qseq_data = {
            os.path.join(self.subname, '11154_42JUYAAXX_c76_l5_r1.fastq'): {
                'istar': True,
                'ispaired': True,
                'sources': [
                    u'woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r1.tar.bz2']
            },
            os.path.join(self.subname, '11154_42JUYAAXX_c76_l5_r2.fastq'): {
                'istar': True,
                'ispaired': True,
                'sources': [
                    u'woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2']
            },
            os.path.join(self.subname, '11154_61MJTAAXX_c76_l6.fastq'): {
                'istar': True,
                'ispaired': False,
                'sources': [
                    u'woldlab_100826_HSI-123_0001_61MJTAAXX_l6_r1.tar.bz2'],
            },
        }
        for args in qseq:
            expected = qseq_data[args['target']]
            self.failUnlessEqual(args['istar'], expected['istar'])
            self.failUnlessEqual(args['ispaired'], expected['ispaired'])
            for i in range(len(expected['sources'])):
                _, filename = os.path.split(args['sources'][i])
                self.failUnlessEqual(filename, expected['sources'][i])


        split_test = dict((( x['target'], x) for x in
            [{'sources': [u'11154_NoIndex_L003_R1_001.fastq.gz',
                         u'11154_NoIndex_L003_R1_002.fastq.gz'],
             'pyscript': 'desplit_fastq.pyc',
             'target': u'11154_C02F9ACXX_c202_l3_r1.fastq'},
            {'sources': [u'11154_NoIndex_L003_R2_001.fastq.gz',
                         u'11154_NoIndex_L003_R2_002.fastq.gz'],
             'pyscript': 'desplit_fastq.pyc',
             'target': u'11154_C02F9ACXX_c202_l3_r2.fastq'}]
         ))
        for arg in split:
            _, target = os.path.split(arg['target'])
            pyscript = split_test[target]['pyscript']
            self.failUnless(arg['pyscript'].endswith(pyscript))
            filename = split_test[target]['target']
            self.failUnless(arg['target'].endswith(filename))
            for s_index in range(len(arg['sources'])):
                s1 = arg['sources'][s_index]
                s2 = split_test[target]['sources'][s_index]
                self.failUnless(s1.endswith(s2))

        #print '-------commands---------'
        #pprint (commands)

    def test_create_scripts(self):
        os.chdir(self.tempdir)
        extract = condorfastq.CondorFastqExtract('host',
                                                 FAKE_APIDATA,
                                                 self.tempdir,
                                                 self.logdir)
        extract.api = FakeApi()
        extract.create_scripts(self.result_map)

        self.failUnless(os.path.exists('srf.condor'))
        with open('srf.condor', 'r') as srf:
            arguments = [ l for l in srf if l.startswith('argument') ]
            arguments.sort()
            self.failUnlessEqual(len(arguments), 2)
            self.failUnless('--single sub-11154/11154_30221AAXX_c33_l4.fastq'
                            in arguments[0])
            self.failUnless(
                '--right sub-11154/11154_30DY0AAXX_c151_l8_r2.fastq' in
                arguments[1])

        self.failUnless(os.path.exists('qseq.condor'))
        with open('qseq.condor', 'r') as srf:
            arguments = [ l for l in srf if l.startswith('argument') ]
            arguments.sort()
            self.failUnlessEqual(len(arguments), 3)
            self.failUnless('-o sub-11154/11154_42JUYAAXX_c76_l5_r1.fastq ' in
                            arguments[0])
            self.failUnless(
                'C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2' in
                arguments[1])
            self.failUnless('61MJTAAXX_c76_l6.fastq -f 61MJTAAXX' in
                            arguments[2])

        self.failUnless(os.path.exists('split_fastq.condor'))
        with open('split_fastq.condor', 'r') as split:
            arguments = [ l for l in split if l.startswith('argument') ]
            arguments.sort()
            self.failUnlessEqual(len(arguments), 2)
            self.failUnless('11154_NoIndex_L003_R1_001.fastq.gz' in \
                            arguments[0])
            self.failUnless('11154_NoIndex_L003_R2_002.fastq.gz' in \
                            arguments[1])

def suite():
    suite = unittest.makeSuite(TestCondorFastq, 'test')
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')

