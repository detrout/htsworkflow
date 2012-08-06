#!/usr/bin/env python
import os
import shutil
import tempfile
import unittest

from htsworkflow.pipelines import sequences


class SequenceFileTests(unittest.TestCase):
    """
    Make sure the sequence archive class works
    """
    def test_get_flowcell_cycle(self):
        tests = [
            ('/root/42BW9AAXX/C1-152',
             sequences.FlowcellPath('42BW9AAXX', 1, 152, None)),
            ('/root/42BW9AAXX/C1-152/',
             sequences.FlowcellPath('42BW9AAXX', 1, 152, None)),
            ('/root/42BW9AAXX/C1-152/Project_12345',
             sequences.FlowcellPath('42BW9AAXX', 1, 152, 'Project_12345')),
            ('/root/42BW9AAXX/C1-152/Project_12345/',
             sequences.FlowcellPath('42BW9AAXX', 1, 152, 'Project_12345')),
        ]

        for t in tests:
            path = sequences.get_flowcell_cycle(t[0])
            self.assertEqual(path, t[1])

    def test_flowcell_cycle(self):
        """
        Make sure code to parse directory heirarchy works
        """
        path = '/root/42BW9AAXX/C1-152'
        flowcell, start, stop, project = sequences.get_flowcell_cycle(path)

        self.assertEqual(flowcell, '42BW9AAXX')
        self.assertEqual(start, 1)
        self.assertEqual(stop, 152)
        self.assertEqual(project, None)

        path = '/root/42BW9AAXX/other'
        self.assertRaises(ValueError, sequences.get_flowcell_cycle, path)

    def test_flowcell_project_cycle(self):
        """
        Make sure code to parse directory heirarchy works
        """
        path = '/root/42BW9AAXX/C1-152/Project_12345_Index1'
        flowcell, start, stop, project = sequences.get_flowcell_cycle(path)

        self.assertEqual(flowcell, '42BW9AAXX')
        self.assertEqual(start, 1)
        self.assertEqual(stop, 152)
        self.assertEqual(project, 'Project_12345_Index1')

        path = '/root/42BW9AAXX/other'
        self.assertRaises(ValueError, sequences.get_flowcell_cycle, path)

    def test_srf(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_4.srf'
        other = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_5.srf'
        pathname = os.path.join(path,name)
        f0 = sequences.parse_srf(path, name)
        f1 = sequences.parse_srf(path, name)
        fother = sequences.parse_srf(path, other)

        self.assertEqual(f0.filetype, 'srf')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<srf 42BW9AAXX 4 %s>" % (pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, 4)
        self.assertEqual(f0.read, None)
        self.assertEqual(f0.pf, None)
        self.assertEqual(f0.cycle, 38)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)


    def test_qseq(self):
        path = '/root/42BW9AAXX/C1-36'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r1.tar.bz2'
        other = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l5_r1.tar.bz2'
        pathname = os.path.join(path,name)
        f0 = sequences.parse_qseq(path, name)
        f1 = sequences.parse_qseq(path, name)
        fother = sequences.parse_qseq(path, other)

        self.assertEqual(f0.filetype, 'qseq')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<qseq 42BW9AAXX 4 %s>" %(pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, 4)
        self.assertEqual(f0.read, 1)
        self.assertEqual(f0.pf, None)
        self.assertEqual(f0.cycle, 36)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)

        path = '/root/ilmn200901/C1-202'
        name = 'woldlab_090125_HWI-EAS_0000_ilmn200901_l1_r1.tar.bz2'
        other = 'woldlab_090125_HWI-EAS_0000_ilmn200901_l1_r2.tar.bz2'
        pathname = os.path.join(path, name)
        f0 = sequences.parse_qseq(path, name)
        f1 = sequences.parse_qseq(path, name)
        fother = sequences.parse_qseq(path, other)

        self.assertEqual(f0.filetype, 'qseq')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<qseq ilmn200901 1 %s>" %(pathname,))
        self.assertEqual(f0.lane, 1)
        self.assertEqual(f0.read, 1)
        self.assertEqual(f0.pf, None)
        self.assertEqual(f0.cycle, 202)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)

    def test_fastq(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r1_pass.fastq.bz2'
        other = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l5_r1_pass.fastq.bz2'
        pathname = os.path.join(path,name)
        f0 = sequences.parse_fastq(path, name)
        f1 = sequences.parse_fastq(path, name)
        fother = sequences.parse_fastq(path, other)

        self.assertEqual(f0.filetype, 'fastq')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<fastq 42BW9AAXX 4 %s>" % (pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, 4)
        self.assertEqual(f0.read, 1)
        self.assertEqual(f0.pf, True)
        self.assertEqual(f0.cycle, 38)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)

        name = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l4_r2_nopass.fastq.bz2'
        other = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2_nopass.fastq.bz2'
        pathname = os.path.join(path,name)
        f0 = sequences.parse_fastq(path, name)
        f1 = sequences.parse_fastq(path, name)
        fother = sequences.parse_fastq(path, other)

        self.assertEqual(f0.filetype, 'fastq')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<fastq 42BW9AAXX 4 %s>" %(pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, 4)
        self.assertEqual(f0.read, 2)
        self.assertEqual(f0.pf, False)
        self.assertEqual(f0.cycle, 38)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)

    def test_project_fastq(self):
        path = '/root/42BW9AAXX/C1-38/Project_12345'
        name = '11111_NoIndex_L001_R1_001.fastq.gz'
        other = '22222_NoIndex_L001_R1_001.fastq.gz'
        pathname = os.path.join(path,name)
        f0 = sequences.parse_fastq(path, name)
        f1 = sequences.parse_fastq(path, name)
        fother = sequences.parse_fastq(path, other)

        self.assertEqual(f0.filetype, 'split_fastq')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<split_fastq 42BW9AAXX 1 %s>" %(pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, 1)
        self.assertEqual(f0.read, 1)
        self.assertEqual(f0.pf, True)
        self.assertEqual(f0.project, '11111')
        self.assertEqual(f0.index, 'NoIndex')
        self.assertEqual(f0.cycle, 38)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)

        name = '11112_AAATTT_L001_R2_003.fastq.gz'
        other = '11112_AAATTT_L002_R2_003.fastq.gz'
        pathname = os.path.join(path,name)
        f0 = sequences.parse_fastq(path, name)
        f1 = sequences.parse_fastq(path, name)
        fother = sequences.parse_fastq(path, other)

        self.assertEqual(f0.filetype, 'split_fastq')
        self.assertEqual(f0.path, pathname)
        self.assertEqual(unicode(f0), unicode(pathname))
        self.assertEqual(repr(f0), "<split_fastq 42BW9AAXX 1 %s>" % (pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, 1)
        self.assertEqual(f0.read, 2)
        self.assertEqual(f0.pf, True)
        self.assertEqual(f0.project, '11112')
        self.assertEqual(f0.index, 'AAATTT')
        self.assertEqual(f0.cycle, 38)
        self.assertEqual(f0.make_target_name('/tmp'),
                         os.path.join('/tmp', name))

        self.assertEqual(f0, f1)
        self.assertNotEqual(f0, fother)

    def test_parse_fastq_pf_flag(self):
        other = 'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2_nopass.fastq.bz2'
        data = ['woldlab', '090622', 'HWI-EAS229', '0120', '42BW9AAXX',
                'l1', 'r2', 'nopass']
        self.assertEqual(sequences.parse_fastq_pf_flag(data), False)

        data = ['woldlab', '090622', 'HWI-EAS229', '0120', '42BW9AAXX',
                'l1', 'r2', 'pass']
        self.assertEqual(sequences.parse_fastq_pf_flag(data), True)

        data = ['woldlab', '090622', 'HWI-EAS229', '0120', '42BW9AAXX',
                'l1', 'r2', 'all']
        self.assertEqual(sequences.parse_fastq_pf_flag(data), None)

        data = ['woldlab', '090622', 'HWI-EAS229', '0120', '42BW9AAXX',
                'l1', 'r2']
        self.assertEqual(sequences.parse_fastq_pf_flag(data), None)

        data = ['woldlab', '090622', 'HWI-EAS229', '0120', '42BW9AAXX',
                'l1', 'r2', 'all', 'newthing']
        self.assertRaises(ValueError, sequences.parse_fastq_pf_flag, data)


    def test_project_fastq_hashing(self):
        """Can we tell the difference between sequence files?
        """
        path = '/root/42BW9AAXX/C1-38/Project_12345'
        names = [('11111_NoIndex_L001_R1_001.fastq.gz',
                  '11111_NoIndex_L001_R2_001.fastq.gz'),
                 ('11112_NoIndex_L001_R1_001.fastq.gz',
                  '11112_NoIndex_L001_R1_002.fastq.gz')
                 ]
        for a_name, b_name in names:
            a = sequences.parse_fastq(path, a_name)
            b = sequences.parse_fastq(path, b_name)
            self.assertNotEqual(a, b)
            self.assertNotEqual(a.key(), b.key())
            self.assertNotEqual(hash(a), hash(b))

    def test_eland(self):
        path = '/root/42BW9AAXX/C1-38'
        name = 's_4_eland_extended.txt.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_eland(path, name)

        self.assertEqual(f.filetype, 'eland')
        self.assertEqual(f.path, pathname)
        self.assertEqual(f.flowcell, '42BW9AAXX')
        self.assertEqual(f.lane, 4)
        self.assertEqual(f.read, None)
        self.assertEqual(f.pf, None)
        self.assertEqual(f.cycle, 38)
        self.assertEqual(f.make_target_name('/tmp'),
                         '/tmp/42BW9AAXX_38_s_4_eland_extended.txt.bz2')

        path = '/root/42BW9AAXX/C1-152'
        name = 's_4_1_eland_extended.txt.bz2'
        pathname = os.path.join(path,name)
        f = sequences.parse_eland(path, name)

        self.assertEqual(f.filetype, 'eland')
        self.assertEqual(f.path, pathname)
        self.assertEqual(f.flowcell, '42BW9AAXX')
        self.assertEqual(f.lane, 4)
        self.assertEqual(f.read, 1)
        self.assertEqual(f.pf, None)
        self.assertEqual(f.cycle, 152)
        self.assertEqual(f.make_target_name('/tmp'),
                         '/tmp/42BW9AAXX_152_s_4_1_eland_extended.txt.bz2')

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
        self.assertEqual(row[0], 4)

    def test_scan_for_sequences(self):
        # simulate tree
        file_types_seen = set()
        file_types_to_see = set(['fastq', 'srf', 'eland', 'qseq'])
        lanes = set()
        lanes_to_see = set((1,2,3))
        with SimulateSimpleTree() as tree:
            seqs = sequences.scan_for_sequences([tree.root, '/a/b/c/98345'])
            for s in seqs:
                self.assertEquals(s.flowcell, '42BW9AAXX')
                self.assertEquals(s.cycle, 33)
                self.assertEquals(s.project, None)
                lanes.add(s.lane)
                file_types_seen.add(s.filetype)

            self.assertEquals(len(seqs), 8)

        self.assertEqual(lanes, lanes_to_see)
        self.assertEqual(file_types_to_see, file_types_seen)
        self.assertRaises(ValueError, sequences.scan_for_sequences, '/tmp')

    def test_scan_for_hiseq_sequences(self):
        # simulate tree
        file_types_seen = set()
        file_types_to_see = set(['split_fastq'])
        lanes = set()
        lanes_to_see = set((1,2))
        projects_seen = set()
        projects_to_see = set(('11111', '21111', '31111'))
        with SimulateHiSeqTree() as tree:
            seqs = sequences.scan_for_sequences([tree.root, '/a/b/c/98345'])
            for s in seqs:
                self.assertEquals(s.flowcell, 'C02AAACXX')
                self.assertEquals(s.cycle, 101)
                lanes.add(s.lane)
                file_types_seen.add(s.filetype)
                projects_seen.add(s.project)

            self.assertEquals(len(seqs), 12)

        self.assertEqual(lanes, lanes_to_see)
        self.assertEqual(file_types_to_see, file_types_seen)
        self.assertEqual(projects_to_see, projects_seen)
        # make sure we require a list, and not the confusing iterating over
        # a string
        self.assertRaises(ValueError, sequences.scan_for_sequences, '/tmp')

class SimulateTree(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.root)

    def mkflowcell(self, *components):
        head = self.root
        for c in components:
            head = os.path.join(head, c)
            if not os.path.exists(head):
                os.mkdir(head)
        return head

    def mkfile(self, flowcell, filename):
        pathname = os.path.join(flowcell, filename)
        stream = open(pathname,'w')
        stream.write(pathname)
        stream.write(os.linesep)
        stream.close()

class SimulateHiSeqTree(SimulateTree):
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix='sequences_')

        files = [
            ('Project_11111', '11111_AAGGCC_L001_R1_001.fastq.gz',),
            ('Project_11111', '11111_AAGGCC_L001_R1_002.fastq.gz',),
            ('Project_11111', '11111_AAGGCC_L001_R2_001.fastq.gz',),
            ('Project_11111', '11111_AAGGCC_L001_R2_002.fastq.gz',),
            ('Project_21111', '21111_TTTTTT_L001_R1_001.fastq.gz',),
            ('Project_21111', '21111_TTTTTT_L001_R1_002.fastq.gz',),
            ('Project_21111', '21111_TTTTTT_L001_R2_001.fastq.gz',),
            ('Project_21111', '21111_TTTTTT_L001_R2_002.fastq.gz',),
            ('Project_31111', '31111_NoIndex_L002_R1_001.fastq.gz',),
            ('Project_31111', '31111_NoIndex_L002_R1_002.fastq.gz',),
            ('Project_31111', '31111_NoIndex_L002_R2_001.fastq.gz',),
            ('Project_31111', '31111_NoIndex_L002_R2_002.fastq.gz',),
            ('.', '11111_AAGGCC_L001_R1_001_export.txt.gz'),
            ('.', '11111_AAGGCC_L001_R1_002_export.txt.gz'),
            ('.', '11111_AAGGCC_L001_R2_001_export.txt.gz'),
            ('.', '11111_AAGGCC_L001_R2_002_export.txt.gz'),
            ('.', '21111_AAGGCC_L001_R1_001_export.txt.gz'),
            ('.', '21111_AAGGCC_L001_R1_002_export.txt.gz'),
            ('.', '21111_AAGGCC_L001_R2_001_export.txt.gz'),
            ('.', '21111_AAGGCC_L001_R2_002_export.txt.gz'),
            ('.', '31111_NoIndex_L002_R1_001_export.txt.gz'),
            ('.', '31111_NoIndex_L002_R1_002_export.txt.gz'),
            ('.', '31111_NoIndex_L002_R2_001_export.txt.gz'),
            ('.', '31111_NoIndex_L002_R2_002_export.txt.gz'),
            ]
        for d, f in files:
            fc = self.mkflowcell(self.root, 'C02AAACXX', 'C1-101', d)
            self.mkfile(fc, f)

class SimulateSimpleTree(SimulateTree):
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix='sequences_')

        fc = self.mkflowcell(self.root, '42BW9AAXX', 'C1-33')
        files = [
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r1.tar.bz2',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2.tar.bz2',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r1.tar.bz2.md5',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2.tar.bz2.md5',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_2.srf',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l3_r1_pass.fastq.bz2',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l3_r2_pass.fastq.bz2',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l3_r1_nopass.fastq.bz2',
            'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l3_r2_nopass.fastq.bz2',
            's_1_eland_extended.txt.bz2',
            's_1_eland_extended.txt.bz2.md5',
            ]
        for f in files:
            self.mkfile(fc, f)


def suite():
    return unittest.makeSuite(SequenceFileTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
