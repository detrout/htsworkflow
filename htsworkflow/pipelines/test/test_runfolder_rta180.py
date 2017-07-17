#!/usr/bin/env python
from __future__ import absolute_import

from datetime import datetime, date
import os
import tempfile
import shutil
from unittest import TestCase

from htsworkflow.pipelines import eland
from htsworkflow.pipelines import ipar
from htsworkflow.pipelines import bustard
from htsworkflow.pipelines import gerald
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines.samplekey import SampleKey
from htsworkflow.pipelines import ElementTree

from .simulate_runfolder import *


def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    flowcell_id = '4286GAAXX'
    runfolder = '090608_HWI-EAS229_0117_{0}'.format(flowcell_id)
    runfolder_dir = os.path.join(temp_dir, runfolder)
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    intensities_dir = make_rta_intensities_1870(data_dir)

    basecalls_dir = make_rta_basecalls_1870(intensities_dir)
    make_matrix_dir_rta160(basecalls_dir)

    gerald_dir = os.path.join(basecalls_dir,
                              'GERALD_07-09-2010_diane')
    os.mkdir(gerald_dir)
    make_gerald_config_100(gerald_dir)
    make_summary_rta160_xml(gerald_dir)
    make_eland_export(gerald_dir, lane_list=[1,2,3,4,5,6,])
    make_scarf(gerald_dir, lane_list=[7,])
    make_fastq(gerald_dir, lane_list=[8,])

    if obj is not None:
        obj.flowcell_id = flowcell_id
        obj.temp_dir = temp_dir
        obj.runfolder = runfolder
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
        self.assertEqual(b.software, 'RTA')
        self.assertEqual(b.version, '1.8.70.0')
        self.assertEqual(b.date,    None)
        self.assertEqual(b.user,    None)
        self.assertEqual(len(b.phasing), 0)

        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.assertEqual(b.software, b2.software)
        self.assertEqual(b.version, b2.version)
        self.assertEqual(b.date,    b2.date )
        self.assertEqual(b.user,    b2.user)

    def test_gerald(self):
        # need to update gerald and make tests for it
        g = gerald.gerald(self.gerald_dir)

        self.assertEqual(g.software, 'GERALD')
        self.assertEqual(g.version, '1.171')
        self.assertEqual(g.date, datetime(2009,2,22,21,15,59))
        self.assertEqual(len(g.lanes), len(g.lanes.keys()))
        self.assertEqual(len(g.lanes), len(g.lanes.items()))


        # list of genomes, matches what was defined up in
        # make_gerald_config.
        # the first None is to offset the genomes list to be 1..9
        # instead of pythons default 0..8
        genomes = [None,
                   '/g/mm9',
                   '/g/mm9',
                   '/g/elegans190',
                   '/g/arabidopsis01222004',
                   '/g/mm9',
                   '/g/mm9',
                   '/g/mm9',
                   '/g/mm9', ]

        # test lane specific parameters from gerald config file
        for i in range(1,9):
            cur_lane = g.lanes[i]
            self.assertEqual(cur_lane.analysis, 'eland_extended')
            self.assertEqual(cur_lane.eland_genome, genomes[i])
            self.assertEqual(cur_lane.read_length, '37')
            self.assertEqual(cur_lane.use_bases, 'Y'*37)

        # I want to be able to use a simple iterator
        for l in g.lanes.values():
          self.assertEqual(l.analysis, 'eland_extended')
          self.assertEqual(l.read_length, '37')
          self.assertEqual(l.use_bases, 'Y'*37)

        # test data extracted from summary file
        clusters = [None,
                    (281331, 11169), (203841, 13513),
                    (220889, 15653), (137294, 14666),
                    (129388, 14525), (262092, 10751),
                    (185754, 13503), (233765, 9537),]

        self.assertEqual(len(g.summary), 1)
        for i in range(1,9):
            summary_lane = g.summary[0][i]
            self.assertEqual(summary_lane.cluster, clusters[i])
            self.assertEqual(summary_lane.lane, i)

        xml = g.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        g2 = gerald.Gerald(xml=xml)

        # do it all again after extracting from the xml file
        self.assertEqual(g.software, g2.software)
        self.assertEqual(g.version, g2.version)
        self.assertEqual(g.date, g2.date)
        self.assertEqual(len(g.lanes.keys()), len(g2.lanes.keys()))
        self.assertEqual(len(g.lanes.items()), len(g2.lanes.items()))

        # test lane specific parameters from gerald config file
        for i in range(1,9):
            g_lane = g.lanes[i]
            g2_lane = g2.lanes[i]
            self.assertEqual(g_lane.analysis, g2_lane.analysis)
            self.assertEqual(g_lane.eland_genome, g2_lane.eland_genome)
            self.assertEqual(g_lane.read_length, g2_lane.read_length)
            self.assertEqual(g_lane.use_bases, g2_lane.use_bases)

        # test (some) summary elements
        self.assertEqual(len(g.summary), 1)
        for i in range(1,9):
            g_summary = g.summary[0][i]
            g2_summary = g2.summary[0][i]
            self.assertEqual(g_summary.cluster, g2_summary.cluster)
            self.assertEqual(g_summary.lane, g2_summary.lane)

            g_eland = g.eland_results
            g2_eland = g2.eland_results
            for lane in g_eland:
                g_results = g_eland[lane]
                g2_results = g2_eland[lane]
                self.assertEqual(g_results.reads,
                                     g2_results.reads)
                if isinstance(g_results, eland.ElandLane):
                  self.assertEqual(len(g_results.mapped_reads),
                                       len(g2_results.mapped_reads))
                  for k in g_results.mapped_reads.keys():
                      self.assertEqual(g_results.mapped_reads[k],
                                           g2_results.mapped_reads[k])

                  self.assertEqual(len(g_results.match_codes),
                                       len(g2_results.match_codes))
                  for k in g_results.match_codes.keys():
                      self.assertEqual(g_results.match_codes[k],
                                           g2_results.match_codes[k])


    def test_eland(self):
        hg_map = {'Lambda.fa': 'Lambda.fa'}
        for i in range(1,22):
          short_name = 'chr%d.fa' % (i,)
          long_name = 'hg18/chr%d.fa' % (i,)
          hg_map[short_name] = long_name

        genome_maps = { 1:hg_map, 2:hg_map, 3:hg_map, 4:hg_map,
                        5:hg_map, 6:hg_map, 7:hg_map, 8:hg_map }
        eland_container = gerald.eland(self.gerald_dir, genome_maps=genome_maps)

        # I added sequence lanes to the last 2 lanes of this test case
        keys = [SampleKey(lane=i, read=1, sample='s') for i in range(1,7)]
        for key in keys:
            lane = eland_container[key]
            self.assertEqual(lane.reads, 28)
            self.assertEqual(lane.sample_name, "s")
            self.assertEqual(lane.lane_id, key.lane)
            self.assertEqual(len(lane.mapped_reads), 7)
            self.assertEqual(lane.mapped_reads['hg18/chr7.fa'], 4)
            self.assertEqual(lane.mapped_reads['Lambda_1-1_11936nts.fa'], 1)
            self.assertEqual(lane.match_codes['U0'], 1)
            self.assertEqual(lane.match_codes['R0'], 20)
            self.assertEqual(lane.match_codes['U1'], 1)
            self.assertEqual(lane.match_codes['R1'], 2)
            self.assertEqual(lane.match_codes['U2'], 11)
            self.assertEqual(lane.match_codes['R2'], 0)
            self.assertEqual(lane.match_codes['NM'], 2)
            self.assertEqual(lane.match_codes['QC'], 9)

        # test scarf
        lane = eland_container[SampleKey(lane=7, read=1, sample='s')]
        self.assertEqual(lane.reads, 5)
        self.assertEqual(lane.sample_name, 's')
        self.assertEqual(lane.lane_id, 7)
        self.assertEqual(lane.sequence_type, eland.SequenceLane.SCARF_TYPE)

        # test fastq
        lane = eland_container[SampleKey(lane=8, read=1, sample='s')]
        self.assertEqual(lane.reads, 3)
        self.assertEqual(lane.sample_name, 's')
        self.assertEqual(lane.lane_id, 8)
        self.assertEqual(lane.sequence_type, eland.SequenceLane.FASTQ_TYPE)

        xml = eland_container.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for key in eland_container:
            l1 = eland_container[key]
            l2 = e2.results[key]
            self.assertEqual(l1.reads, l2.reads)
            self.assertEqual(l1.sample_name, l2.sample_name)
            self.assertEqual(l1.lane_id, l2.lane_id)
            if isinstance(l1, eland.ElandLane):
              self.assertEqual(len(l1.mapped_reads), len(l2.mapped_reads))
              self.assertEqual(len(l1.mapped_reads), 7)
              for k in l1.mapped_reads.keys():
                  self.assertEqual(l1.mapped_reads[k],
                                       l2.mapped_reads[k])

              self.assertEqual(len(l1.match_codes), 9)
              self.assertEqual(len(l1.match_codes), len(l2.match_codes))
              for k in l1.match_codes.keys():
                  self.assertEqual(l1.match_codes[k],
                                       l2.match_codes[k])
            elif isinstance(l1, eland.SequenceLane):
                self.assertEqual(l1.sequence_type, l2.sequence_type)

    def test_runfolder(self):
        runs = runfolder.get_runs(self.runfolder_dir)

        # do we get the flowcell id from the filename?
        self.assertEqual(len(runs), 1)
        name = 'run_4286GAAXX_%s.xml' % ( date.today().strftime('%Y-%m-%d'),)        
        self.assertEqual(runs[0].serialization_filename, name)
        self.assertEqual(runs[0].runfolder_name, '090220_HWI-EAS229_0093_30VR0AAXX')

        # do we get the flowcell id from the FlowcellId.xml file
        make_flowcell_id(self.runfolder_dir, '207BTAAXY')
        runs = runfolder.get_runs(self.runfolder_dir)
        self.assertEqual(len(runs), 1)
        name = 'run_207BTAAXY_%s.xml' % ( date.today().strftime('%Y-%m-%d'),)
        self.assertEqual(runs[0].serialization_filename, name)



        r1 = runs[0]
        xml = r1.get_elements()
        xml_str = ElementTree.tostring(xml)

        r2 = runfolder.PipelineRun(xml=xml)
        self.assertEqual(r1.serialization_filename, r2.serialization_filename)
        self.assertNotEqual(r2.image_analysis, None)
        self.assertNotEqual(r2.bustard, None)
        self.assertNotEqual(r2.gerald, None)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(RunfolderTests))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
