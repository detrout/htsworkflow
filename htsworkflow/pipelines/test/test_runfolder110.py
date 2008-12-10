#!/usr/bin/env python

from datetime import datetime, date
import os
import tempfile
import shutil
import unittest

from htsworkflow.pipelines import firecrest
from htsworkflow.pipelines import bustard
from htsworkflow.pipelines import gerald
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines.runfolder import ElementTree

from htsworkflow.pipelines.test.simulate_runfolder import *


def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(temp_dir,
                                 '081017_HWI-EAS229_0062_30J55AAXX')
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    firecrest_dir = os.path.join(data_dir,
                                 'C1-37_Firecrest1.9.6_20-10-2008_diane')
    os.mkdir(firecrest_dir)

    matrix_dir = os.path.join(firecrest_dir, 'Matrix')
    os.mkdir(matrix_dir)
    make_matrix(matrix_dir)

    bustard_dir = os.path.join(firecrest_dir,
                               'Bustard1.9.6_20-10-2008_diane')
    os.mkdir(bustard_dir)
    make_phasing_params(bustard_dir)

    gerald_dir = os.path.join(bustard_dir,
                              'GERALD_20-10-2008_diane')
    os.mkdir(gerald_dir)
    make_gerald_config(gerald_dir)
    make_summary_htm_110(gerald_dir)
    make_eland_multi(gerald_dir)

    if obj is not None:
        obj.temp_dir = temp_dir
        obj.runfolder_dir = runfolder_dir
        obj.data_dir = data_dir
        obj.image_analysis_dir = firecrest_dir
        obj.matrix_dir = matrix_dir
        obj.bustard_dir = bustard_dir
        obj.gerald_dir = gerald_dir


class RunfolderTests(unittest.TestCase):
    """
    Test components of the runfolder processing code
    which includes firecrest, bustard, and gerald
    """
    def setUp(self):
        # attaches all the directories to the object passed in
        make_runfolder(self)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_firecrest(self):
        """
        Construct a firecrest object
        """
        f = firecrest.firecrest(self.image_analysis_dir)
        self.failUnlessEqual(f.version, '1.9.6')
        self.failUnlessEqual(f.start, 1)
        self.failUnlessEqual(f.stop, 37)
        self.failUnlessEqual(f.user, 'diane')
        self.failUnlessEqual(f.date, date(2008,10,20))

        xml = f.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)

        f2 = firecrest.Firecrest(xml=xml)
        self.failUnlessEqual(f.version, f2.version)
        self.failUnlessEqual(f.start,   f2.start)
        self.failUnlessEqual(f.stop,    f2.stop)
        self.failUnlessEqual(f.user,    f2.user)

    def test_bustard(self):
        """
        construct a bustard object
        """
        b = bustard.bustard(self.bustard_dir)
        self.failUnlessEqual(b.version, '1.9.6')
        self.failUnlessEqual(b.date,    date(2008,10,20))
        self.failUnlessEqual(b.user,    'diane')
        self.failUnlessEqual(len(b.phasing), 8)
        self.failUnlessAlmostEqual(b.phasing[8].phasing, 0.0099)

        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.failUnlessEqual(b.version, b2.version)
        self.failUnlessEqual(b.date,    b2.date )
        self.failUnlessEqual(b.user,    b2.user)
        self.failUnlessEqual(len(b.phasing), len(b2.phasing))
        for key in b.phasing.keys():
            self.failUnlessEqual(b.phasing[key].lane,
                                 b2.phasing[key].lane)
            self.failUnlessEqual(b.phasing[key].phasing,
                                 b2.phasing[key].phasing)
            self.failUnlessEqual(b.phasing[key].prephasing,
                                 b2.phasing[key].prephasing)

    def test_gerald(self):
        # need to update gerald and make tests for it
        g = gerald.gerald(self.gerald_dir)

        self.failUnlessEqual(g.version,
            '@(#) Id: GERALD.pl,v 1.68.2.2 2007/06/13 11:08:49 km Exp')
        self.failUnlessEqual(g.date, datetime(2008,4,19,19,8,30))
        self.failUnlessEqual(len(g.lanes), len(g.lanes.keys()))
        self.failUnlessEqual(len(g.lanes), len(g.lanes.items()))


        # list of genomes, matches what was defined up in
        # make_gerald_config.
        # the first None is to offset the genomes list to be 1..9
        # instead of pythons default 0..8
        genomes = [None, '/g/dm3', '/g/equcab1', '/g/equcab1', '/g/canfam2',
                         '/g/hg18', '/g/hg18', '/g/hg18', '/g/hg18', ]

        # test lane specific parameters from gerald config file
        for i in range(1,9):
            cur_lane = g.lanes[i]
            self.failUnlessEqual(cur_lane.analysis, 'eland')
            self.failUnlessEqual(cur_lane.eland_genome, genomes[i])
            self.failUnlessEqual(cur_lane.read_length, '32')
            self.failUnlessEqual(cur_lane.use_bases, 'Y'*32)

        # I want to be able to use a simple iterator
        for l in g.lanes.values():
          self.failUnlessEqual(l.analysis, 'eland')
          self.failUnlessEqual(l.read_length, '32')
          self.failUnlessEqual(l.use_bases, 'Y'*32)

        # raw cluster numbers extracted from summary file
        # its the first +/- value in the lane results summary
        # section
        clusters = [None,
                    (190220, 15118), (190560, 14399),
                    (187597, 12369), (204142, 16877),
                    (247308, 11600), (204298, 15640),
                    (202707, 15404), (198075, 14702),]

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

        self.failUnlessEqual(len(g.summary), 1)
        # test (some) summary elements
        for i in range(1,9):
            g_summary = g.summary[0][i]
            g2_summary = g2.summary[0][i]
            self.failUnlessEqual(g_summary.cluster, g2_summary.cluster)
            self.failUnlessEqual(g_summary.lane, g2_summary.lane)

            g_eland = g.eland_results
            g2_eland = g2.eland_results
            for lane in g_eland.keys():
                self.failUnlessEqual(g_eland[lane].reads,
                                     g2_eland[lane].reads)
                self.failUnlessEqual(len(g_eland[lane].mapped_reads),
                                     len(g2_eland[lane].mapped_reads))
                for k in g_eland[lane].mapped_reads.keys():
                    self.failUnlessEqual(g_eland[lane].mapped_reads[k],
                                         g2_eland[lane].mapped_reads[k])

                self.failUnlessEqual(len(g_eland[lane].match_codes),
                                     len(g2_eland[lane].match_codes))
                for k in g_eland[lane].match_codes.keys():
                    self.failUnlessEqual(g_eland[lane].match_codes[k],
                                         g2_eland[lane].match_codes[k])


    def test_eland(self):
        hg_map = {'Lambda.fa': 'Lambda.fa'}
        for i in range(1,22):
          short_name = 'chr%d.fa' % (i,)
          long_name = 'hg18/chr%d.fa' % (i,)
          hg_map[short_name] = long_name

        genome_maps = { 1:hg_map, 2:hg_map, 3:hg_map, 4:hg_map,
                        5:hg_map, 6:hg_map, 7:hg_map, 8:hg_map }
        eland = gerald.eland(self.gerald_dir, genome_maps=genome_maps)

        for i in range(1,9):
            lane = eland[i]
            self.failUnlessEqual(lane.reads, 4)
            self.failUnlessEqual(lane.sample_name, "s")
            self.failUnlessEqual(lane.lane_id, i)
            self.failUnlessEqual(len(lane.mapped_reads), 15)
            self.failUnlessEqual(lane.mapped_reads['hg18/chr5.fa'], 4)
            self.failUnlessEqual(lane.match_codes['U0'], 1)
            self.failUnlessEqual(lane.match_codes['R0'], 2)
            self.failUnlessEqual(lane.match_codes['U1'], 1)
            self.failUnlessEqual(lane.match_codes['R1'], 9)
            self.failUnlessEqual(lane.match_codes['U2'], 0)
            self.failUnlessEqual(lane.match_codes['R2'], 12)
            self.failUnlessEqual(lane.match_codes['NM'], 1)
            self.failUnlessEqual(lane.match_codes['QC'], 0)

        xml = eland.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for i in range(1,9):
            l1 = eland[i]
            l2 = e2[i]
            self.failUnlessEqual(l1.reads, l2.reads)
            self.failUnlessEqual(l1.sample_name, l2.sample_name)
            self.failUnlessEqual(l1.lane_id, l2.lane_id)
            self.failUnlessEqual(len(l1.mapped_reads), len(l2.mapped_reads))
            self.failUnlessEqual(len(l1.mapped_reads), 15)
            for k in l1.mapped_reads.keys():
                self.failUnlessEqual(l1.mapped_reads[k],
                                     l2.mapped_reads[k])

            self.failUnlessEqual(len(l1.match_codes), 9)
            self.failUnlessEqual(len(l1.match_codes), len(l2.match_codes))
            for k in l1.match_codes.keys():
                self.failUnlessEqual(l1.match_codes[k],
                                     l2.match_codes[k])

    def test_runfolder(self):
        runs = runfolder.get_runs(self.runfolder_dir)

        # do we get the flowcell id from the filename?
        self.failUnlessEqual(len(runs), 1)
        name = 'run_30J55AAXX_2008-10-20.xml'
        self.failUnlessEqual(runs[0].name, name)

        # do we get the flowcell id from the FlowcellId.xml file
        make_flowcell_id(self.runfolder_dir, '30J55AAXX')
        runs = runfolder.get_runs(self.runfolder_dir)
        self.failUnlessEqual(len(runs), 1)
        name = 'run_30J55AAXX_2008-10-20.xml'
        self.failUnlessEqual(runs[0].name, name)

        r1 = runs[0]
        xml = r1.get_elements()
        xml_str = ElementTree.tostring(xml)

        r2 = runfolder.PipelineRun(xml=xml)
        self.failUnlessEqual(r1.name, r2.name)
        self.failIfEqual(r2.image_analysis, None)
        self.failIfEqual(r2.bustard, None)
        self.failIfEqual(r2.gerald, None)


def suite():
    return unittest.makeSuite(RunfolderTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")

