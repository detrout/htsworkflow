#!/usr/bin/env python
import os
import unittest

from htsworkflow.pipelines import sequences

class SequenceFileTests(unittest.TestCase):
    """
    Make sure the sequence archive class works
    """
    def test_flowcell_cycle(self):
        """
        Make sure code to parse directory heirarchy works
        """
        path = '/root/42BW9AAXX/C1-152'
        flowcell, start, stop = sequences.get_flowcell_cycle(path)

        self.failUnlessEqual(flowcell, '42BW9AAXX')
        self.failUnlessEqual(start, 1)
        self.failUnlessEqual(stop, 152)

        path = '/root/42BW9AAXX/other'
        self.failUnlessRaises(ValueError, sequences.get_flowcell_cycle, path)


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
        self.failUnlessEqual(f.cycle, 38)

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
        self.failUnlessEqual(f.cycle, 36)


        path = '/root/ilmn200901/C1-202'
        name = 'woldlab_090125_HWI-EAS_0000_ilmn200901_l1_r1.tar.bz2'
        pathname = os.path.join(path, name)
        f = sequences.parse_qseq(path, name)

        self.failUnlessEqual(f.filetype, 'qseq')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.lane, 1)
        self.failUnlessEqual(f.read, 1)
        self.failUnlessEqual(f.pf, None)
        self.failUnlessEqual(f.cycle, 202)

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
        self.failUnlessEqual(f.cycle, 38)

        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r2_nopass.fastq.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_fastq(path, name)

        self.failUnlessEqual(f.filetype, 'fastq')
        self.failUnlessEqual(f.path, pathname)
        self.failUnlessEqual(f.flowcell, '42BW9AAXX')
        self.failUnlessEqual(f.lane, 4)
        self.failUnlessEqual(f.read, 2)
        self.failUnlessEqual(f.pf, False)
        self.failUnlessEqual(f.cycle, 38)

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
        self.failUnlessEqual(f.cycle, 38)

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
        self.failUnlessEqual(f.cycle, 152)

    def test_sequence_file_equality(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r1.tar.bz2'

        f1_qseq = sequences.parse_qseq(path, name)
        f2_qseq = sequences.parse_qseq(path, name)

        self.failUnlessEqual(f1_qseq, f2_qseq)

    def test_sql(self):
        """
        Make sure that the quick and dirty sql interface in sequences works
        """
        import sqlite3
        db = sqlite3.connect(":memory:")
        c = db.cursor()
        sequences.create_sequence_table(c)
        
        data = [('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r1.tar.bz2'),
                ('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2.tar.bz2'),
                ('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l2_r1.tar.bz2'),
                ('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l2_r21.tar.bz2'),]

        for path, name in data:
            seq = sequences.parse_qseq(path, name)
            seq.save(c)

        count = c.execute("select count(*) from sequences")
        row = count.fetchone()
        self.failUnlessEqual(row[0], 4)
 

def suite():
    return unittest.makeSuite(SequenceFileTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
