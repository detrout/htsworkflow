#!/usr/bin/env python

from datetime import datetime, date
import glob
import os
import tempfile
import shutil
from unittest2 import TestCase

from htsworkflow.pipelines import bustard
from htsworkflow.pipelines import eland
from htsworkflow.pipelines import gerald
from htsworkflow.pipelines import ipar
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines import srf
from htsworkflow.pipelines.runfolder import ElementTree

from htsworkflow.pipelines.test.simulate_runfolder import *

FCID = 'AA01AAABXX'
RUN_NAME = '110420_SN787_0069_%s' %( FCID,)

def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(temp_dir, RUN_NAME)
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    intensities_dir = make_rta_intensities_1_10(data_dir)

    basecalls_dir = make_rta_basecalls_1_10(intensities_dir)
    make_matrix_dir_rta_1_10(basecalls_dir)
    make_qseqs(basecalls_dir, ABXX_BASE_CALL_INFO)

    gerald_dir = os.path.join(basecalls_dir,
                              'GERALD_02-05-2011_diane')
    os.mkdir(gerald_dir)
    make_gerald_config_1_7(gerald_dir)
    make_summary_casava1_7_xml(gerald_dir)
    make_eland_export(gerald_dir, lane_list=[4,5,6,7,8])
    make_fastq(gerald_dir, lane_list=[1,2,3,])

    if obj is not None:
        obj.temp_dir = temp_dir
        obj.runfolder_dir = runfolder_dir
        obj.data_dir = data_dir
        obj.image_analysis_dir = intensities_dir
        obj.bustard_dir = basecalls_dir
        obj.gerald_dir = gerald_dir


class RunfolderTests(TestCase):
    """
    Test components of the runfolder processing code
    which includes firecrest, bustard, and gerald
    """
    def setUp(self):
        # attaches all the directories to the object passed in
        make_runfolder(self)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_bustard(self):
        """Construct a bustard object"""
        b = bustard.bustard(self.bustard_dir)
        self.failUnlessEqual(b.software, 'RTA')
        self.failUnlessEqual(b.version, '1.10.36.0')
        self.failUnlessEqual(b.date,    None)
        self.failUnlessEqual(b.user,    None)
        self.failUnlessEqual(len(b.phasing), 0)

        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.failUnlessEqual(b.software, b2.software)
        self.failUnlessEqual(b.version,  b2.version)
        self.failUnlessEqual(b.date,     b2.date )
        self.failUnlessEqual(b.user,     b2.user)

    def test_gerald(self):
        # need to update gerald and make tests for it
        g = gerald.gerald(self.gerald_dir)

        self.failUnlessEqual(g.software, 'CASAVA')
        self.failUnlessEqual(g.version, '1.7.0')
        self.failUnlessEqual(g.date, datetime(2011,5,2,19,19,49))
        self.failUnlessEqual(len(g.lanes), len(g.lanes.keys()))
        self.failUnlessEqual(len(g.lanes), len(g.lanes.items()))


        # list of genomes, matches what was defined up in
        # make_gerald_config.
        # the first None is to offset the genomes list to be 1..9
        # instead of pythons default 0..8
        genomes = [None, # placeholder
                   None, # no genome
                   None, # no genome
                   None, # no genome
                   '/g/hg18',
                   '/g/elegans190',
                   '/g/elegans190',
                   '/g/elegans190',
                   '/g/phi', ]
        analysis = [None, # placeholder
                    'sequence_pair',
                    'sequence_pair',
                    'sequence_pair',
                    'eland_pair',
                    'eland_pair',
                    'eland_pair',
                    'eland_pair',
                    'eland_pair',]


        # test lane specific parameters from gerald config file
        for i in range(1,9):
            cur_lane = g.lanes[i]
            self.failUnlessEqual(cur_lane.analysis, analysis[i])
            self.failUnlessEqual(cur_lane.eland_genome, genomes[i])
            self.failUnlessEqual(cur_lane.read_length, '100')
            self.failUnlessEqual(cur_lane.use_bases, 'Y'*100+'y'*100)

        # I want to be able to use a simple iterator
        for l in g.lanes.values():
          self.failUnless(l.analysis in ('sequence_pair', 'eland_pair'))
          self.failUnlessEqual(l.read_length, '100')
          self.failUnlessEqual(l.use_bases, 'Y'*100+'y'*100)

        # test data extracted from summary file
        clusters = [None,
                    (1073893, 146344), (1671038, 167728),
                    (5778484, 83123),  (2411032, 290873),
                    (2197555, 294381), (2725097, 333724),
                    (2549849, 313056), (2282159, 232709),]

        self.failUnlessEqual(len(g.summary), 1)
        for i in range(1,9):
            summary_lane = g.summary[0][i]
            self.failUnlessEqual(summary_lane.cluster, clusters[i])
            self.failUnlessEqual(summary_lane.lane, i)

        xml = g.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        g2 = gerald.Gerald(xml=xml)

        # do it all again after extracting from the xml file
        self.failUnlessEqual(g.software, g2.software)
        self.failUnlessEqual(g.version, g2.version)
        self.failUnlessEqual(g.date, g2.date)
        self.failUnlessEqual(len(g.lanes.keys()), len(g2.lanes.keys()))
        self.failUnlessEqual(len(g.lanes.items()), len(g2.lanes.items()))

        # test lane specific parameters from gerald config file
        for i in range(1,9):
            g_lane = g.lanes[i]
            g2_lane = g2.lanes[i]
            self.failUnlessEqual(g_lane.analysis, g2_lane.analysis)
            self.failUnlessEqual(g_lane.eland_genome, g2_lane.eland_genome)
            self.failUnlessEqual(g_lane.read_length, g2_lane.read_length)
            self.failUnlessEqual(g_lane.use_bases, g2_lane.use_bases)

        # test (some) summary elements
        self.failUnlessEqual(len(g.summary), 1)
        for i in range(1,9):
            g_summary = g.summary[0][i]
            g2_summary = g2.summary[0][i]
            self.failUnlessEqual(g_summary.cluster, g2_summary.cluster)
            self.failUnlessEqual(g_summary.lane, g2_summary.lane)

            g_eland = g.eland_results
            g2_eland = g2.eland_results
            for key in g_eland:
                g_results = g_eland[key]
                g2_results = g2_eland[key]
                self.failUnlessEqual(g_results.reads,
                                     g2_results.reads)
                if isinstance(g_results, eland.ElandLane):
                  self.failUnlessEqual(len(g_results.mapped_reads),
                                       len(g2_results.mapped_reads))
                  for k in g_results.mapped_reads.keys():
                      self.failUnlessEqual(g_results.mapped_reads[k],
                                           g2_results.mapped_reads[k])

                  self.failUnlessEqual(len(g_results.match_codes),
                                       len(g2_results.match_codes))
                  for k in g_results.match_codes.keys():
                      self.failUnlessEqual(g_results.match_codes[k],
                                           g2_results.match_codes[k])


    def test_eland(self):
        ls_tree(self.runfolder_dir)
        hg_map = {'Lambda.fa': 'Lambda.fa'}
        for i in range(1,22):
          short_name = 'chr%d.fa' % (i,)
          long_name = 'hg18/chr%d.fa' % (i,)
          hg_map[short_name] = long_name

        genome_maps = { 1:hg_map, 2:hg_map, 3:hg_map, 4:hg_map,
                        5:hg_map, 6:hg_map, 7:hg_map, 8:hg_map }
        eland_container = gerald.eland(self.gerald_dir, genome_maps=genome_maps)

        # test fastq
        for i in range(1,4):
            key = eland.SampleKey(lane=i, read=1, sample='s')
            lane = eland_container[key]
            self.failUnlessEqual(lane.reads, 3)
            self.failUnlessEqual(lane.sample_name, 's')
            self.failUnlessEqual(lane.lane_id, i)
            self.failUnlessEqual(lane.sequence_type,
                                 eland.SequenceLane.FASTQ_TYPE)

        # I added sequence lanes to the last 2 lanes of this test case
        for i in range(4,9):
            key = eland.SampleKey(lane=i, read=1, sample='s')
            lane = eland_container[key]
            self.failUnlessEqual(lane.reads, 28)
            self.failUnlessEqual(lane.sample_name, "s")
            self.failUnlessEqual(lane.lane_id, i)
            self.failUnlessEqual(len(lane.mapped_reads), 7)
            self.failUnlessEqual(lane.mapped_reads['hg18/chr7.fa'], 4)
            self.failUnlessEqual(lane.match_codes['U0'], 1)
            self.failUnlessEqual(lane.match_codes['R0'], 20)
            self.failUnlessEqual(lane.match_codes['U1'], 1)
            self.failUnlessEqual(lane.match_codes['R1'], 2)
            self.failUnlessEqual(lane.match_codes['U2'], 11)
            self.failUnlessEqual(lane.match_codes['R2'], 0)
            self.failUnlessEqual(lane.match_codes['NM'], 2)
            self.failUnlessEqual(lane.match_codes['QC'], 9)


        xml = eland_container.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for key in eland_container:
            l1 = eland_container[key]
            l2 = e2[key]
            self.failUnlessEqual(l1.reads, l2.reads)
            self.failUnlessEqual(l1.sample_name, l2.sample_name)
            self.failUnlessEqual(l1.lane_id, l2.lane_id)
            if isinstance(l1, eland.ElandLane):
              self.failUnlessEqual(len(l1.mapped_reads), len(l2.mapped_reads))
              self.failUnlessEqual(len(l1.mapped_reads), 7)
              for k in l1.mapped_reads.keys():
                  self.failUnlessEqual(l1.mapped_reads[k],
                                       l2.mapped_reads[k])

              self.failUnlessEqual(len(l1.match_codes), 9)
              self.failUnlessEqual(len(l1.match_codes), len(l2.match_codes))
              for k in l1.match_codes.keys():
                  self.failUnlessEqual(l1.match_codes[k],
                                       l2.match_codes[k])
            elif isinstance(l1, eland.SequenceLane):
                self.failUnlessEqual(l1.sequence_type, l2.sequence_type)

    def test_runfolder(self):
        runs = runfolder.get_runs(self.runfolder_dir)

        # do we get the flowcell id from the filename?
        self.failUnlessEqual(len(runs), 1)
        name = 'run_%s_%s.xml' % ( FCID, date.today().strftime('%Y-%m-%d'),)
        self.failUnlessEqual(runs[0].name, name)

        # do we get the flowcell id from the FlowcellId.xml file
        make_flowcell_id(self.runfolder_dir, FCID)
        runs = runfolder.get_runs(self.runfolder_dir)
        self.failUnlessEqual(len(runs), 1)
        name = 'run_%s_%s.xml' % ( FCID, date.today().strftime('%Y-%m-%d'),)
        self.failUnlessEqual(runs[0].name, name)

        r1 = runs[0]
        xml = r1.get_elements()
        xml_str = ElementTree.tostring(xml)

        r2 = runfolder.PipelineRun(xml=xml)
        self.failUnlessEqual(r1.name, r2.name)
        self.failIfEqual(r2.image_analysis, None)
        self.failIfEqual(r2.bustard, None)
        self.failIfEqual(r2.gerald, None)

    def test_srf(self):
        pattern_list = srf.create_qseq_patterns(self.bustard_dir)
        self.assertEqual(len(pattern_list), 1)
        pattern = pattern_list[0][1] % (1,)
        self.assertEqual(
            glob.fnmatch.fnmatch("s_1_1_1101_qseq.txt", pattern),
            True)
        self.assertEqual(
            glob.fnmatch.fnmatch("s_1_0001_qseq.txt", pattern),
            False)

        print pattern


def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(RunfolderTests))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
