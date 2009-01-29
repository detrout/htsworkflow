#!/usr/bin/env python

from datetime import datetime, date
import os
import tempfile
import shutil
import unittest

from gaworkflow.pipeline import firecrest
from gaworkflow.pipeline import bustard
from gaworkflow.pipeline import gerald
from gaworkflow.pipeline import runfolder
from gaworkflow.pipeline.runfolder import ElementTree

from gaworkflow.pipeline.test.simulate_runfolder import *


def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(temp_dir,
                                 '080102_HWI-EAS229_0010_207BTAAXX')
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    ipar_dir = make_firecrest_dir(data_dir, "1.9.6", 1, 152)

    matrix_dir = os.path.join(ipar_dir, 'Matrix')
    os.mkdir(matrix_dir)
    make_matrix(matrix_dir)

    bustard_dir = os.path.join(ipar_dir,
                               'Bustard1.8.28_12-04-2008_diane')
    os.mkdir(bustard_dir)
    make_phasing_params(bustard_dir)

    gerald_dir = os.path.join(bustard_dir,
                              'GERALD_12-04-2008_diane')
    os.mkdir(gerald_dir)
    make_gerald_config(gerald_dir)
    make_summary_paired_htm(gerald_dir)
    make_eland_multi(gerald_dir, paired=True)

    if obj is not None:
        obj.temp_dir = temp_dir
        obj.runfolder_dir = runfolder_dir
        obj.data_dir = data_dir
        obj.image_analysis_dir = ipar_dir
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
        self.failUnlessEqual(f.stop, 152)
        self.failUnlessEqual(f.user, 'diane')
        # As of 2008-12-8, the date was being set in 
        # simulate_runfolder.make_firecrest_dir
        self.failUnlessEqual(f.date, date(2008,4,12))

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
        self.failUnlessEqual(b.version, '1.8.28')
        self.failUnlessEqual(b.date,    date(2008,4,12))
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

        # test data extracted from summary file
        clusters = [[None,
                    (103646, 4515), (106678, 4652),
                    (84583, 5963), (68813, 4782),
                    (104854, 4664), (43555, 1632),
                    (54265, 1588), (64363, 2697),],
                    [None,
                    (103647, 4516), (106679, 4653),
                    (84584, 5964), (68814, 4783),
                    (104855, 4665), (43556, 1633),
                    (54266, 1589), (64364, 2698),],]

        for end in [0,1]:
            for lane in range(1,9):
                summary_lane = g.summary[end][lane]
                self.failUnlessEqual(summary_lane.cluster, clusters[end][lane])
                self.failUnlessEqual(summary_lane.lane, lane)

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

        # test (some) summary elements
        for end in [0,1]:
            for i in range(1,9):
                g_summary = g.summary[end][i]
                g2_summary = g2.summary[end][i]
                self.failUnlessEqual(g_summary.cluster, g2_summary.cluster)
                self.failUnlessEqual(g_summary.lane, g2_summary.lane)

                g_eland = g.eland_results
                g2_eland = g2.eland_results
                for lane in g_eland.results[end].keys():
                    g_results = g_eland.results[end][lane]
                    g2_results = g_eland.results[end][lane]
                    self.failUnlessEqual(g_results.reads,
                                         g2_results.reads)
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
        hg_map = {'Lambda.fa': 'Lambda.fa'}
        for i in range(1,22):
          short_name = 'chr%d.fa' % (i,)
          long_name = 'hg18/chr%d.fa' % (i,)
          hg_map[short_name] = long_name

        genome_maps = { 1:hg_map, 2:hg_map, 3:hg_map, 4:hg_map,
                        5:hg_map, 6:hg_map, 7:hg_map, 8:hg_map }
        eland = gerald.eland(self.gerald_dir, genome_maps=genome_maps)

        # check first end
        for i in range(1,9):
            lane = eland.results[0][i]
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

        # check second end
        for i in range(1,9):
            lane = eland.results[1][i]
            self.failUnlessEqual(lane.reads, 5)
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
            self.failUnlessEqual(lane.match_codes['QC'], 1)

        xml = eland.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for end in [0, 1]:
            for i in range(1,9):
                l1 = eland.results[end][i]
                l2 = e2.results[end][i]
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
        # firecrest's date depends on filename not the create time.
        name = 'run_207BTAAXX_2008-04-19.xml'
        self.failUnlessEqual(runs[0].name, name)

        # do we get the flowcell id from the FlowcellId.xml file
        make_flowcell_id(self.runfolder_dir, '207BTAAXY')
        runs = runfolder.get_runs(self.runfolder_dir)
        self.failUnlessEqual(len(runs), 1)
        name = 'run_207BTAAXY_2008-04-19.xml'
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

