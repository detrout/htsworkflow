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
from htsworkflow.pipelines import ElementTree

from .simulate_runfolder import *


def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(temp_dir,
                                 '090313_HWI-EAS229_0101_3021JAAXX')
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    ipar_dir = make_ipar_dir(data_dir, '1.30')

    bustard_dir = os.path.join(ipar_dir,
                               'Bustard1.3.2_15-03-2008_diane')
    os.mkdir(bustard_dir)
    make_phasing_params(bustard_dir)
    make_bustard_config132(bustard_dir)

    gerald_dir = os.path.join(bustard_dir,
                              'GERALD_15-03-2008_diane')
    os.mkdir(gerald_dir)
    make_gerald_config_100(gerald_dir)
    make_summary_ipar130_htm(gerald_dir)
    make_eland_multi(gerald_dir, lane_list=[1,2,3,4,5,6,])
    make_scarf(gerald_dir, lane_list=[7,])
    make_fastq(gerald_dir, lane_list=[8,])

    if obj is not None:
        obj.temp_dir = temp_dir
        obj.runfolder_dir = runfolder_dir
        obj.data_dir = data_dir
        obj.image_analysis_dir = ipar_dir
        obj.bustard_dir = bustard_dir
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

    def test_ipar(self):
        """
        Construct a firecrest object
        """
        i = ipar.ipar(self.image_analysis_dir)
        self.assertEqual(i.software, 'IPAR')
        self.assertEqual(i.version, '2.01.192.0')
        self.assertEqual(i.start, 1)
        self.assertEqual(i.stop, 37)

        xml = i.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)

        i2 = ipar.IPAR(xml=xml)
        self.assertEqual(i.software, i2.software)
        self.assertEqual(i.version, i2.version)
        self.assertEqual(i.start,   i2.start)
        self.assertEqual(i.stop,    i2.stop)
        self.assertEqual(i.date,    i2.date)
        self.assertEqual(i.file_list(), i2.file_list())

    def test_bustard(self):
        """
        construct a bustard object
        """
        def check_crosstalk(crosstalk):
            self.assertAlmostEqual(crosstalk.base['A'][0],  1.27)
            self.assertAlmostEqual(crosstalk.base['A'][1],  0.20999999999999)
            self.assertAlmostEqual(crosstalk.base['A'][2], -0.02)
            self.assertAlmostEqual(crosstalk.base['A'][3], -0.03)

            self.assertAlmostEqual(crosstalk.base['C'][0],  0.57)
            self.assertAlmostEqual(crosstalk.base['C'][1],  0.58)
            self.assertAlmostEqual(crosstalk.base['C'][2], -0.01)
            self.assertAlmostEqual(crosstalk.base['C'][3], -0.01)

            self.assertAlmostEqual(crosstalk.base['T'][0], -0.02)
            self.assertAlmostEqual(crosstalk.base['T'][1], -0.02)
            self.assertAlmostEqual(crosstalk.base['T'][2],  0.80)
            self.assertAlmostEqual(crosstalk.base['T'][3],  1.07)

            self.assertAlmostEqual(crosstalk.base['G'][0], -0.03)
            self.assertAlmostEqual(crosstalk.base['G'][1], -0.04)
            self.assertAlmostEqual(crosstalk.base['G'][2],  1.51)
            self.assertAlmostEqual(crosstalk.base['G'][3], -0.02)

        b = bustard.bustard(self.bustard_dir)
        self.assertEqual(b.software, 'Bustard')
        self.assertEqual(b.version, '1.3.2')
        self.assertEqual(b.date,    date(2008,3,15))
        self.assertEqual(b.user,    'diane')
        self.assertEqual(len(b.phasing), 8)
        self.assertAlmostEqual(b.phasing[8].phasing, 0.0099)
        self.assertEqual(set(b.crosstalk.base), set(['A','C','T','G']))
        check_crosstalk(b.crosstalk)

        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.assertEqual(b.software, b2.software)
        self.assertEqual(b.version, b2.version)
        self.assertEqual(b.date,    b2.date )
        self.assertEqual(b.user,    b2.user)
        self.assertEqual(len(b.phasing), len(b2.phasing))
        for key in b.phasing.keys():
            self.assertEqual(b.phasing[key].lane,
                                 b2.phasing[key].lane)
            self.assertEqual(b.phasing[key].phasing,
                                 b2.phasing[key].phasing)
            self.assertEqual(b.phasing[key].prephasing,
                                 b2.phasing[key].prephasing)
        check_crosstalk(b2.crosstalk)

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
                    (126910, 4300), (165739, 6792),
                    (196565, 8216), (153897, 8501),
                    (135536, 3908), (154083, 9315),
                    (159991, 9292), (198479, 17671),]

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
            for key in g_eland:
                g_results = g_eland[key]
                g2_results = g2_eland[key]
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
        for key in eland_container:
            lane = eland_container[key]
            if key.lane in [1,2,3,4,5,6]:
                self.assertEqual(lane.reads, 6)
                self.assertEqual(lane.sample_name, "s")
                self.assertEqual(lane.lane_id, key.lane)
                self.assertEqual(len(lane.mapped_reads), 17)
                self.assertEqual(lane.mapped_reads['hg18/chr5.fa'], 4)
                self.assertEqual(lane.match_codes['U0'], 3)
                self.assertEqual(lane.match_codes['R0'], 2)
                self.assertEqual(lane.match_codes['U1'], 1)
                self.assertEqual(lane.match_codes['R1'], 9)
                self.assertEqual(lane.match_codes['U2'], 0)
                self.assertEqual(lane.match_codes['R2'], 12)
                self.assertEqual(lane.match_codes['NM'], 1)
                self.assertEqual(lane.match_codes['QC'], 0)
            elif key.lane == 7:
                self.assertEqual(lane.reads, 5)
                self.assertEqual(lane.sample_name, 's')
                self.assertEqual(lane.lane_id, 7)
                self.assertEqual(lane.sequence_type,
                                     eland.SequenceLane.SCARF_TYPE)
            elif key.lane == 8:
                self.assertEqual(lane.reads, 3)
                self.assertEqual(lane.sample_name, 's')
                self.assertEqual(lane.lane_id, 8)
                self.assertEqual(lane.sequence_type,
                                     eland.SequenceLane.FASTQ_TYPE)

        xml = eland_container.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for key in eland_container:
            l1 = eland_container[key]
            l2 = e2[key]
            self.assertEqual(l1.reads, l2.reads)
            self.assertEqual(l1.sample_name, l2.sample_name)
            self.assertEqual(l1.lane_id, l2.lane_id)
            if isinstance(l1, eland.ElandLane):
              self.assertEqual(len(l1.mapped_reads), len(l2.mapped_reads))
              self.assertEqual(len(l1.mapped_reads), 17)
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
        name = 'run_3021JAAXX_%s.xml' % ( date.today().strftime('%Y-%m-%d'),)
        self.assertEqual(runs[0].serialization_filename, name)

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
