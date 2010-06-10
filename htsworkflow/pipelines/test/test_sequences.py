#!/usr/bin/env python
import os
import unittest

from htsworkflow.pipelines import sequences

class SequenceFileTests(unittest.TestCase):
    """
    Make sure the sequence archive class works
    """
    def test_srf(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_4.srf'
        pathname = os.path.join(path,name)
        f = sequences.parse_srf(path, name)

        self.failUnlessEqual(f.filetype, 'srf')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, None)
        self.failUnlessEqual(f.pf, None)
        self.failUnlessEqual(f.cycle, None)

    def test_qseq(self):
        path = '/root/42BW9AAXX/C1-36'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r1.tar.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_qseq(path, name)

        self.failUnlessEqual(f.filetype, 'qseq')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, 1)
        self.failUnlessEqual(f.pf, None)
        self.failUnlessEqual(f.cycle, None)

    def test_fastq(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r1_pass.fastq.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_fastq(path, name)

        self.failUnlessEqual(f.filetype, 'fastq')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, 1)
        self.failUnlessEqual(f.pf, True)
        self.failUnlessEqual(f.cycle, None)

        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r2_nopass.fastq.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_fastq(path, name)

        self.failUnlessEqual(f.filetype, 'fastq')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, 2)
        self.failUnlessEqual(f.pf, False)
        self.failUnlessEqual(f.cycle, None)

    def test_eland(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 's_4_eland_extended.txt.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_eland(path, name)

        self.failUnlessEqual(f.filetype, 'eland')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, None)
        self.failUnlessEqual(f.pf, None)
        self.failUnlessEqual(f.cycle, 'C1-38')

        path = '/root/42BW9AAXX/C1-152'
        name = 's_4_1_eland_extended.txt.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_eland(path, name)

        self.failUnlessEqual(f.filetype, 'eland')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, 1)
        self.failUnlessEqual(f.pf, None)
        self.failUnlessEqual(f.cycle, 'C1-152')

    def test_sequence_file_equality(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r1.tar.bz2'

        f1_qseq = sequences.parse_qseq(path, name)
        f2_qseq = sequences.parse_qseq(path, name)

        self.failUnlessEqual(f1_qseq, f2_qseq)

def suite():
    return unittest.makeSuite(SequenceFileTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
