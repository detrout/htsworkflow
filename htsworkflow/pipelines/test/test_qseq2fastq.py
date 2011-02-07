#!/usr/bin/env python

import unittest

import htsworkflow.pipelines.qseq2fastq as qseq2fastq

class TestQseq2Fastq(unittest.TestCase):
    def test_parse_slice(self):
        s = qseq2fastq.parse_slice("1:")
        self.failUnlessEqual(s.start, 1)
        self.failUnlessEqual(s.stop, None)

        s = qseq2fastq.parse_slice("0:2")
        self.failUnlessEqual(s.start, 0)
        self.failUnlessEqual(s.stop, 2)

def suite():
    return unittest.makeSuite(TestQseq2Fastq, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
    
