"""Test wrappers around ucsc file formats
"""
import os
from unittest2 import TestCase
from htsworkflow.util.test import TEST_DATA_DIR
from htsworkflow.util.ucsc import bigWigInfo

from distutils.spawn import find_executable

class TestUCSC(TestCase):
    def test_bigwig_info(self):
        if not find_executable('bigWigInfo'):
            self.skipTest('Need bigWigInfo on path to test')

        filename = os.path.join(TEST_DATA_DIR, 'foo.bigWig')
        info = bigWigInfo(filename)
        self.assertEqual(info.version, 4)
        self.assertEqual(info.isCompressed, True)
        # what should i do for byteswapped arch?
        self.assertEqual(info.isSwapped, True)
        self.assertEqual(info.primaryDataSize, 48)
        self.assertEqual(info.primaryIndexSize, 6204)
        self.assertEqual(info.zoomLevels, 2)
        self.assertEqual(info.basesCovered, 30)
        self.assertAlmostEqual(info.mean, 0.0)
        self.assertAlmostEqual(info.min, -5.5)
        self.assertAlmostEqual(info.max, 5.5)
        self.assertAlmostEqual(info.std, 4.567501)
        
