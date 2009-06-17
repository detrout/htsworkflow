import os
import unittest
from StringIO import StringIO

from simulate_runfolder import TESTDATA_DIR
from htsworkflow.pipelines.runfolder import load_pipeline_run_xml

class testLoadRunXML(unittest.TestCase):
    def testVerson0(self):
        runxml_path = os.path.join(TESTDATA_DIR, 'run_FC12150_2007-09-27.xml')
        run = load_pipeline_run_xml(runxml_path)
        eland_summary_by_lane = run.gerald.eland_results.results[0]
        assert len(eland_summary_by_lane) == 8

    def testVerson1(self):
        runxml_path = os.path.join(TESTDATA_DIR, 'run_207B2AAXX_2008-04-12.xml')
        run = load_pipeline_run_xml(runxml_path)
        eland_summary_by_lane = run.gerald.eland_results.results[0]
        assert len(eland_summary_by_lane) == 8
        
def suite():
    return unittest.makeSuite(testLoadRunXML,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
