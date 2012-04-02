#!/usr/bin/env python

import copy
import os
from pprint import pprint
import shutil
import tempfile
import unittest

from htsworkflow.submission.results import ResultMap

S1_NAME = '1000-sample'
S2_NAME = '2000-sample'

S1_FILES = [
    os.path.join(S1_NAME, 'file1_l8_r1.fastq'),
    os.path.join(S1_NAME, 'file1_l8_r2.fastq'),
]

S2_FILES = [
    os.path.join(S2_NAME, 'file1.bam'),
    os.path.join(S2_NAME, 'file1_l5.fastq'),
]

def generate_sample_results_tree(obj):
    obj.tempdir = tempfile.mkdtemp(prefix="results_test")
    obj.sourcedir = os.path.join(obj.tempdir, 'source')
    obj.resultdir = os.path.join(obj.tempdir, 'results')

    for d in [obj.sourcedir,
              os.path.join(obj.sourcedir, S1_NAME),
              os.path.join(obj.sourcedir, S2_NAME),
              obj.resultdir]:
        os.mkdir(os.path.join(obj.tempdir, d))

    tomake = []
    tomake.extend(S1_FILES)
    tomake.extend(S2_FILES)
    for f in tomake:
        stream = open(os.path.join(obj.sourcedir, f), 'w')
        stream.write(f)
        stream.close()

class TestResultMap(unittest.TestCase):
    def setUp(self):
        generate_sample_results_tree(self)

    def tearDown(self):
        shutil.rmtree(self.tempdir)


    def test_dict_like(self):
        """Make sure the result map works like an ordered dictionary
        """
        results = ResultMap()
        results.add_result('1000', 'dir1000')
        results.add_result('2000', 'dir2000')
        results.add_result('1500', 'dir1500')

        self.failUnlessEqual(results.keys(), ['1000', '2000', '1500'])
        self.failUnlessEqual(list(results.values()),
                             ['dir1000', 'dir2000', 'dir1500'])
        self.failUnlessEqual(list(results.items()),
                             [('1000', 'dir1000'),
                              ('2000', 'dir2000'),
                              ('1500', 'dir1500')])

        self.failUnlessEqual(results['1000'], 'dir1000')
        self.failUnlessEqual(results['1500'], 'dir1500')
        self.failUnlessEqual(results['2000'], 'dir2000')

    def test_make_from(self):
        results = ResultMap()
        results.add_result('1000', S1_NAME)
        results.add_result('2000', S2_NAME)

        results.make_tree_from(self.sourcedir, self.resultdir)

        sample1_dir = os.path.join(self.resultdir, S1_NAME)
        sample2_dir = os.path.join(self.resultdir, S2_NAME)
        self.failUnless(os.path.isdir(sample1_dir))
        self.failUnless(os.path.isdir(sample2_dir))

        for f in S1_FILES + S2_FILES:
            self.failUnless(
                os.path.islink(
                    os.path.join(self.resultdir, f)))




def suite():
    suite = unittest.makeSuite(TestResultMap, 'test')
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')

