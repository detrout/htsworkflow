#!/usr/bin/env python

from datetime import datetime, date
import logging
import os
import tempfile
import shutil
import sys
import unittest

from htsworkflow.pipelines import eland
from htsworkflow.pipelines import ipar
from htsworkflow.pipelines import bustard
from htsworkflow.pipelines import gerald
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines.runfolder import ElementTree

from htsworkflow.pipelines.test.simulate_runfolder import *

logging.basicConfig(level=logging.ERROR)

def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(temp_dir,
                                 '090608_HWI-EAS229_0117_4286GAAXX')
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    intensities_dir = make_rta_intensities_1460(data_dir)

    bustard_dir = os.path.join(intensities_dir, 'Bustard1.4.0_16-06-2009_diane')
    os.mkdir(bustard_dir)
    make_phasing_params(bustard_dir)
    make_bustard_config132(bustard_dir)
    score_dir = make_scores(bustard_dir)
    make_qseqs(bustard_dir)

    gerald_dir = os.path.join(bustard_dir,
                              'GERALD_16-06-2009_diane')
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
        obj.image_analysis_dir = intensities_dir
        obj.bustard_dir = bustard_dir
        obj.gerald_dir = gerald_dir


class RunfolderExtractTests(unittest.TestCase):
    """
    Test the extract result code.
    """
    def setUp(self):
        # attaches all the directories to the object passed in
        make_runfolder(self)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_extract_results(self):
        runs = runfolder.get_runs(self.runfolder_dir)
        self.failUnlessEqual(len(runs), 1)
        runfolder.extract_results(runs, self.temp_dir, site='asite')
        archive = os.listdir(os.path.join(self.temp_dir, '4286GAAXX', 'C1-38'))
        self.failUnlessEqual(len(archive), 34)
        self.failUnless('asite_090608_HWI-EAS229_0117_4286GAAXX_l6_r1.tar.bz2' in archive)

        
def suite():
    return unittest.makeSuite(RunfolderExtractTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")

