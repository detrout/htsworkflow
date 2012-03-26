#!/usr/bin/env python
import os
from StringIO import StringIO
import unittest

from htsworkflow.pipelines import summary
from simulate_runfolder import TESTDATA_DIR

class SummaryTests(unittest.TestCase):
    """Test elements of the summary file parser
    """
    def test_is_xml(self):
        xmlfile = StringIO('<?xml version="1.0"?>\n<tag>\n')
        htmlfile = StringIO('<html>\n<head></head>\n<body><p></p></body>\n</html>')

        self.failUnlessEqual(summary.isxml_stream(xmlfile), True)
        self.failUnlessEqual(xmlfile.tell(), 0)

        self.failUnlessEqual(summary.isxml_stream(htmlfile), False)

    def test_xml_summary_file(self):
        pathname = os.path.join(TESTDATA_DIR, 'Summary-casava1.7.xml')
        s = summary.Summary(pathname)
        self.failUnlessEqual(len(s.lane_results[0]), 8)
        self.failUnlessEqual(s.lane_results[0][1].cluster, (1073893, 146344))

    def test_html_summary_file(self):
        pathname = os.path.join(TESTDATA_DIR, 'Summary-ipar130.htm')
        s = summary.Summary(pathname)
        self.failUnlessEqual(len(s.lane_results[0]), 8)
        self.failUnlessEqual(s.lane_results[0][1].cluster, (126910, 4300))

    def test_hiseq_sample_summary_file(self):
        pathname = os.path.join(TESTDATA_DIR, 'sample_summary_1_12.htm')
        s = summary.Summary(pathname)

def suite():
    return unittest.makeSuite(SummaryTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
