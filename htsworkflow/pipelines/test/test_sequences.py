#!/usr/bin/env python
import os
import shutil
import tempfile
from unittest import TestCase

import RDF

from htsworkflow.pipelines import sequences
from htsworkflow.util.rdfhelp import get_model, load_string_into_model, \
     rdfNS, libraryOntology, dump_model, fromTypedNode

class SequenceFileTests(TestCase):
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<srf 42BW9AAXX 4 %s>" % (pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, '4')
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<qseq 42BW9AAXX 4 %s>" %(pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, '4')
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<qseq ilmn200901 1 %s>" %(pathname,))
        self.assertEqual(f0.lane, '1')
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<fastq 42BW9AAXX 4 %s>" % (pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, '4')
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<fastq 42BW9AAXX 4 %s>" %(pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, '4')
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<split_fastq 42BW9AAXX 1 %s>" %(pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, '1')
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
        self.assertEqual(str(f0), str(pathname))
        self.assertEqual(repr(f0), "<split_fastq 42BW9AAXX 1 %s>" % (pathname,))
        self.assertEqual(f0.flowcell, '42BW9AAXX')
        self.assertEqual(f0.lane, '1')
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
        self.assertEqual(f.lane, '4')
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
        self.assertEqual(f.lane, '4')
        self.assertEqual(f.read, 1)
        self.assertEqual(f.pf, None)
        self.assertEqual(f.cycle, 152)
        self.assertEqual(f.make_target_name('/tmp'),
                         '/tmp/42BW9AAXX_152_s_4_1_eland_extended.txt.bz2')

    def _generate_sequences(self):
        seqs = []
        data = [('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r1.tar.bz2'),
                ('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2.tar.bz2'),
                ('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l2_r1.tar.bz2'),
                ('/root/42BW9AAXX/C1-152',
                'woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l2_r21.tar.bz2'),]

        for path, name in data:
            seqs.append(sequences.parse_qseq(path, name))

        path = '/root/42BW9AAXX/C1-38/Project_12345'
        name = '12345_AAATTT_L003_R1_001.fastq.gz'
        pathname = os.path.join(path,name)
        seqs.append(sequences.parse_fastq(path, name))
        self.assertEqual(len(seqs), 5)
        return seqs


    def test_sql(self):
        """
        Make sure that the quick and dirty sql interface in sequences works
        """
        import sqlite3
        db = sqlite3.connect(":memory:")
        c = db.cursor()
        sequences.create_sequence_table(c)

        for seq in self._generate_sequences():
            seq.save_to_sql(c)

        count = c.execute("select count(*) from sequences")
        row = count.fetchone()
        self.assertEqual(row[0], 5)

    def test_basic_rdf_scan(self):
        """Make sure we can save to RDF model"""
        import RDF
        model = get_model()

        for seq in self._generate_sequences():
            seq.save_to_model(model)

        files = list(model.find_statements(
            RDF.Statement(None,
                          rdfNS['type'],
                          libraryOntology['IlluminaResult'])))
        self.assertEqual(len(files), 5)
        files = list(model.find_statements(
            RDF.Statement(None,
                          libraryOntology['file_type'],
                          libraryOntology['qseq'])))
        self.assertEqual(len(files), 4)
        files = list(model.find_statements(
            RDF.Statement(None,
                          libraryOntology['file_type'],
                          libraryOntology['split_fastq'])))
        self.assertEqual(len(files), 1)

        files = list(model.find_statements(
            RDF.Statement(None, libraryOntology['library_id'], None)))
        self.assertEqual(len(files), 1)

        files = list(model.find_statements(
            RDF.Statement(None, libraryOntology['flowcell_id'], None)))
        self.assertEqual(len(files), 5)

        files = list(model.find_statements(
            RDF.Statement(None, libraryOntology['flowcell'], None)))
        self.assertEqual(len(files), 0)

        files = list(model.find_statements(
            RDF.Statement(None, libraryOntology['library'], None)))
        self.assertEqual(len(files), 0)

    def test_rdf_scan_with_url(self):
        """Make sure we can save to RDF model"""
        import RDF
        model = get_model()
        base_url = 'http://localhost'
        for seq in self._generate_sequences():
            seq.save_to_model(model, base_url=base_url)
        localFC = RDF.NS(base_url + '/flowcell/')
        localLibrary = RDF.NS(base_url + '/library/')

        files = list(model.find_statements(
            RDF.Statement(None, libraryOntology['flowcell'], None)))
        self.assertEqual(len(files), 5)
        for f in files:
            self.assertEqual(f.object, localFC['42BW9AAXX/'])

        files = list(model.find_statements(
            RDF.Statement(None, libraryOntology['library'], None)))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].object, localLibrary['12345'])

    def test_rdf_fixup_library(self):
        """Make sure we can save to RDF model"""
        base_url = 'http://localhost'
        localLibrary = RDF.NS(base_url + '/library/')

        flowcellInfo = """@prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#> .

<{base}/flowcell/42BW9AAXX/>
    libns:flowcell_id "42BW9AXX"@en ;
    libns:has_lane <{base}/lane/1169>, <{base}/lane/1170>,
                   <{base}/lane/1171>, <{base}/lane/1172> ;
    libns:read_length 75 ;
    a libns:IlluminaFlowcell .

<{base}/lane/1169>
    libns:lane_number "1" ; libns:library <{base}/library/10923/> .
<{base}/lane/1170>
    libns:lane_number "2" ; libns:library <{base}/library/10924/> .
<{base}/lane/1171>
    libns:lane_number "3" ; libns:library <{base}/library/12345/> .
<{base}/lane/1172>
    libns:lane_number "3" ; libns:library <{base}/library/10930/> .
""".format(base=base_url)
        model = get_model()
        load_string_into_model(model, 'turtle', flowcellInfo)
        for seq in self._generate_sequences():
            seq.save_to_model(model)
        f = sequences.update_model_sequence_library(model, base_url=base_url)

        libTerm = libraryOntology['library']
        libIdTerm = libraryOntology['library_id']

        url = 'file:///root/42BW9AAXX/C1-152/woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l1_r2.tar.bz2'
        nodes = list(model.get_targets(RDF.Uri(url), libTerm))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0], localLibrary['10923/'])
        nodes = list(model.get_targets(RDF.Uri(url), libIdTerm))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(fromTypedNode(nodes[0]), '10923')

        url = 'file:///root/42BW9AAXX/C1-152/woldlab_090622_HWI-EAS229_0120_42BW9AAXX_l2_r1.tar.bz2'
        nodes = list(model.get_targets(RDF.Uri(url), libTerm))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0], localLibrary['10924/'])
        nodes = list(model.get_targets(RDF.Uri(url), libIdTerm))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(fromTypedNode(nodes[0]), '10924')

        url = 'file:///root/42BW9AAXX/C1-38/Project_12345/12345_AAATTT_L003_R1_001.fastq.gz'
        nodes = list(model.get_targets(RDF.Uri(url), libTerm))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0], localLibrary['12345/'])
        nodes = list(model.get_targets(RDF.Uri(url), libIdTerm))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(fromTypedNode(nodes[0]), '12345')

    def test_load_from_model(self):
        """Can we round trip through a RDF model"""
        model = get_model()
        path = '/root/42BW9AAXX/C1-38/Project_12345/'
        filename = '12345_AAATTT_L003_R1_001.fastq.gz'
        seq = sequences.parse_fastq(path, filename)
        seq.save_to_model(model)

        seq_id = 'file://'+path+filename
        seqNode = RDF.Node(RDF.Uri(seq_id))
        libNode = RDF.Node(RDF.Uri('http://localhost/library/12345'))
        model.add_statement(
            RDF.Statement(seqNode, libraryOntology['library'], libNode))
        seq2 = sequences.SequenceFile.load_from_model(model, seq_id)

        self.assertEqual(seq.flowcell, seq2.flowcell)
        self.assertEqual(seq.flowcell, '42BW9AAXX')
        self.assertEqual(seq.filetype, seq2.filetype)
        self.assertEqual(seq2.filetype, 'split_fastq')
        self.assertEqual(seq.lane, seq2.lane)
        self.assertEqual(seq2.lane, '3')
        self.assertEqual(seq.read, seq2.read)
        self.assertEqual(seq2.read, 1)
        self.assertEqual(seq.project, seq2.project)
        self.assertEqual(seq2.project, '12345')
        self.assertEqual(seq.index, seq2.index)
        self.assertEqual(seq2.index, 'AAATTT')
        self.assertEqual(seq.split, seq2.split)
        self.assertEqual(seq2.split, '001')
        self.assertEqual(seq.cycle, seq2.cycle)
        self.assertEqual(seq.pf, seq2.pf)
        self.assertEqual(seq2.libraryNode, libNode)
        self.assertEqual(seq.path, seq2.path)

    def test_scan_for_sequences(self):
        # simulate tree
        file_types_seen = set()
        file_types_to_see = set(['fastq', 'srf', 'eland', 'qseq'])
        lanes = set()
        lanes_to_see = set(('1','2','3'))
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
        lanes_to_see = set(('1','2'))
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
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(SequenceFileTests))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
