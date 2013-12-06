#!/usr/bin/env python

from datetime import datetime, date
import os
import tempfile
import shutil
from unittest2 import TestCase

from htsworkflow.pipelines.test.simulate_runfolder import TESTDATA_DIR

from htsworkflow.pipelines import eland
from htsworkflow.pipelines import ipar
from htsworkflow.pipelines import bustard
from htsworkflow.pipelines import gerald
from htsworkflow.pipelines import runfolder

class AlignmentFreeRunfolderTests(TestCase):
    def test_loading(self):
        run_xml = os.path.join(TESTDATA_DIR, 'run_C23KDACXX_2013-05-11.xml')
        run = runfolder.load_pipeline_run_xml(run_xml)
        self.assertEqual(run.runfolder_name, '130508_SN787_0146_BC23KDACXX')

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(AlignmentFreeRunfolderTests))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
