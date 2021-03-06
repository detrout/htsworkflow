#!/usr/bin/env python
from __future__ import absolute_import

from datetime import datetime, date
import logging
import os
import tempfile
import shutil
from unittest import TestCase

from htsworkflow.pipelines import eland
from htsworkflow.pipelines.samplekey import SampleKey
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
    flowcell_id = 'D07K6ACXX'
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(
        temp_dir,
        '110815_SN787_0101_A{0}'.format(flowcell_id))
    os.mkdir(runfolder_dir)

    make_runinfo(runfolder_dir, flowcell_id)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    intensities_dir = make_rta_intensities_1_12(data_dir)
    make_status_rta1_12(data_dir)

    basecalls_dir = make_rta_basecalls_1_12(intensities_dir)
    make_matrix_dir_rta_1_12(basecalls_dir)

    unaligned_dir = os.path.join(runfolder_dir, "Unaligned")
    os.mkdir(unaligned_dir)
    make_unaligned_fastqs_1_12(unaligned_dir, flowcell_id)
    make_unaligned_config_1_12(unaligned_dir)
    make_unaligned_status_1_12(unaligned_dir, flowcell_id)

    aligned_dir = os.path.join(runfolder_dir, "Aligned")
    os.mkdir(aligned_dir)
    make_aligned_eland_export(aligned_dir, flowcell_id)
    make_aligned_config_1_12(aligned_dir)

    if obj is not None:
        obj.flowcell_id = flowcell_id
        obj.temp_dir = temp_dir
        obj.runfolder_dir = runfolder_dir
        obj.data_dir = data_dir
        obj.image_analysis_dir = intensities_dir
        obj.bustard_dir = unaligned_dir
        obj.gerald_dir = aligned_dir
        obj.reads = 2


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
        self.assertEqual(b.version, '1.12.4.2')
        self.assertEqual(b.date,    None)
        self.assertEqual(b.user,    None)
        self.assertEqual(len(b.phasing), 0)

        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.assertEqual(b.software, b2.software)
        self.assertEqual(b.version,  b2.version)
        self.assertEqual(b.date,     b2.date )
        self.assertEqual(b.user,     b2.user)

    def test_gerald(self):
        # need to update gerald and make tests for it
        g = gerald.gerald(self.gerald_dir)

        self.assertEqual(g.software, 'CASAVA')
        self.assertEqual(g.version, '1.8.1')
        self.assertEqual(len(g.lanes), len(g.lanes.keys()))
        self.assertEqual(len(g.lanes), len(g.lanes.items()))

        # list of genomes, matches what was defined up in
        # make_gerald_config.
        # the first None is to offset the genomes list to be 1..9
        # instead of pythons default 0..8
        # test lane specific parameters from gerald config file

        undetermined = g.lanes[SampleKey(sample='Undetermined_indices')]
        self.assertEqual(undetermined.analysis, 'none')
        self.assertEqual(undetermined.read_length, None)
        self.assertEqual(undetermined.use_bases, None)

        project = g.lanes[SampleKey(sample='11115')]
        self.assertEqual(project.analysis, 'eland_extended')
        self.assertEqual(project.eland_genome, '/g/hg18/chromosomes/')
        self.assertEqual(project.read_length, '49')
        self.assertEqual(project.use_bases, 'y'*49+'n')

        # test data extracted from summary file
        clusters = [None,
                    (3878755,  579626.0), (3920639, 1027332.4),
                    (5713049,  876187.3), (5852907,  538640.6),
                    (4006751, 1265247.4), (5678021,  627070.7),
                    (1854131,  429053.2), (4777517,  592904.0),
                   ]

        self.assertEqual(len(g.summary), self.reads)
        for i in range(1,9):
            summary_lane = g.summary[0][i]
            self.assertEqual(summary_lane.cluster, clusters[i])
            self.assertEqual(summary_lane.lane, i)

        xml = g.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        g2 = gerald.CASAVA(xml=xml)

        # do it all again after extracting from the xml file
        self.assertEqual(g.software, g2.software)
        self.assertEqual(g.version, g2.version)
        self.assertEqual(g.date, g2.date)
        self.assertEqual(len(g.lanes.keys()), len(g2.lanes.keys()))
        self.assertEqual(len(g.lanes.items()), len(g2.lanes.items()))

        # test lane specific parameters from gerald config file
        for i in g.lanes.keys():
            g_lane = g.lanes[i]
            g2_lane = g2.lanes[i]
            self.assertEqual(g_lane.analysis, g2_lane.analysis)
            self.assertEqual(g_lane.eland_genome, g2_lane.eland_genome)
            self.assertEqual(g_lane.read_length, g2_lane.read_length)
            self.assertEqual(g_lane.use_bases, g2_lane.use_bases)

        # test (some) summary elements
        self.assertEqual(len(g.summary), self.reads)
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

        samples = set(('11111', '11112', '11113', '11114', '11115',
                       '11116', '11117', '11118', '11119', '11120'))
        genome_maps = {}
        for i in range(1,9):
            genome_maps[i] = hg_map

        eland_container = gerald.eland(self.gerald_dir, genome_maps=genome_maps)

        for lane in eland_container.values():
            # I added sequence lanes to the last 2 lanes of this test case
            if lane.sample_name == '11113':
                self.assertEqual(lane.reads, 24)
                self.assertEqual(lane.mapped_reads['hg18/chr9.fa'], 6)
                self.assertEqual(lane.match_codes['U0'], 6)
                self.assertEqual(lane.match_codes['R0'], 18)
                self.assertEqual(lane.match_codes['R1'], 24)
                self.assertEqual(lane.match_codes['R2'], 18)
                self.assertEqual(lane.match_codes['NM'], 12)
            else:
                self.assertEqual(lane.reads, 8)
                self.assertEqual(lane.mapped_reads['hg18/chr9.fa'], 2)
                self.assertEqual(lane.match_codes['U0'], 2)
                self.assertEqual(lane.match_codes['R0'], 6)
                self.assertEqual(lane.match_codes['R1'], 8)
                self.assertEqual(lane.match_codes['R2'], 6)
                self.assertEqual(lane.match_codes['NM'], 4)

            self.assertTrue(lane.sample_name in samples)
            #self.assertEqual(lane.lane_id, 1)
            self.assertEqual(len(lane.mapped_reads), 1)
            self.assertEqual(lane.match_codes['U1'], 0)
            self.assertEqual(lane.match_codes['U2'], 0)
            self.assertEqual(lane.match_codes['QC'], 0)

        xml = eland_container.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for key in eland_container.results:
            l1 = eland_container.results[key]
            l2 = e2.results[key]
            self.assertEqual(l1.reads, l2.reads)
            self.assertEqual(l1.sample_name, l2.sample_name)
            self.assertEqual(l1.lane_id, l2.lane_id)
            if isinstance(l1, eland.ElandLane):
              self.assertEqual(len(l1.mapped_reads), len(l2.mapped_reads))
              self.assertEqual(len(l1.mapped_reads), 1)
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
        self.assertEqual(runs[0].flowcell_id, self.flowcell_id)
        name = 'run_%s_%s.xml' % ( self.flowcell_id,
                                   date.today().strftime('%Y-%m-%d'),)
        self.assertEqual(runs[0].serialization_filename, name)

        bustard_dir = os.path.join(self.runfolder_dir, 'Unaligned')
        r1 = runs[0]
        self.assertEqual(r1.bustard.sequence_format, 'fastq')
        self.assertEqual(r1.bustard.pathname, bustard_dir)
        self.assertEqual(r1.gerald.runfolder_name, 'Unaligned')

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
