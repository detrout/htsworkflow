import os
from unittest2 import TestCase
from StringIO import StringIO

from simulate_runfolder import TESTDATA_DIR
from htsworkflow.pipelines.runfolder import load_pipeline_run_xml

from htsworkflow.pipelines.eland import SampleKey


class testLoadRunXML(TestCase):
    def _check_run_xml(self, run_xml_name, results, eland_results=8):
        run_xml_path = os.path.join(TESTDATA_DIR, run_xml_name)
        run = load_pipeline_run_xml(run_xml_path)

        self.failUnlessEqual(run.image_analysis.start, results['cycle_start'])
        self.failUnlessEqual(run.image_analysis.stop, results['cycle_stop'])

        query = SampleKey(read=1)
        eland_summary_by_lane = run.gerald.eland_results.find_keys(query)
        self.failUnlessEqual(len(list(eland_summary_by_lane)), eland_results)

        runfolder_name = results['runfolder_name']
        self.failUnlessEqual(run.runfolder_name, runfolder_name)
        self.failUnlessEqual(run.gerald.runfolder_name, runfolder_name)

        for (end, lane), lane_results in results['lane_results'].items():
            for name, test_value in lane_results.items():
                xml_value = getattr(run.gerald.summary[end][lane], name)

                self.failUnlessEqual(xml_value, test_value,
                    "%s[%s][%s]: %s %s != %s" % (run_xml_name, end, lane, name, xml_value, test_value))

    def testVersion0(self):
        run_xml_name = 'run_FC12150_2007-09-27.xml'
        results = {'runfolder_name': '070924_USI-EAS44_0022_FC12150',
                   'cycle_start': 1,
                   'cycle_stop': 36,
                   'lane_results': {
                       # end, lane
                       (0, 1): {
                           'average_alignment_score': (12116.63, 596.07),
                           'average_first_cycle_intensity': (500,36),
                           'cluster': (31261, 6010),
                           'cluster_pass_filter': None,
                           'percent_error_rate': (2.07, 0.38),
                           'percent_intensity_after_20_cycles': (74.74, 3.78),
                           'percent_pass_filter_align': None,
                           'percent_pass_filter_clusters': (27.38, 7.31),
                           }
                       }
                   }
        self._check_run_xml(run_xml_name, results, eland_results=0)

    def testVersion1(self):

        run_xml_name = 'run_207B2AAXX_2008-04-12.xml'
        results = {'runfolder_name': '080408_HWI-EAS229_0023_207B2AAXX',
                   'cycle_start': 1,
                   'cycle_stop': 33,
                   'lane_results': {
                       # end, lane
                       }
                   }
        self._check_run_xml(run_xml_name, results, eland_results=8)

    def testVersion2(self):
        run_xml_name = 'run_62DJMAAXX_2011-01-09.xml'
        results = {'runfolder_name': '101229_ILLUMINA-EC5D15_00026_62DJMAAXX',
                   'cycle_start': 1,
                   'cycle_stop': 152,
                   'lane_results': {
                       # end, lane
                       (0, 2): {
                           'average_alignment_score': (171.98, 1.4),
                           'average_first_cycle_intensity': (381, 5),
                           'cluster': (443170, 10241),
                           'cluster_pass_filter': (362709, 8335),
                           'percent_error_rate': (4.13, 0.14),
                           'percent_intensity_after_20_cycles': (85.89, 3.26),
                           'percent_pass_filter_align': (79.73, 0.23),
                           'percent_pass_filter_clusters': (81.85, 0.8),
                           },
                       (0, 5): {
                           'average_alignment_score': None,
                           'average_first_cycle_intensity': (362, 4),
                           'cluster': (310619, 15946),
                           'cluster_pass_filter': (277584, 13858),
                           'percent_error_rate': None,
                           'percent_intensity_after_20_cycles': (90.35, 1.12),
                           'percent_pass_filter_align': None,
                           'percent_pass_filter_clusters': (89.37, 0.25),
                           }
                       }
                   }
        self._check_run_xml(run_xml_name, results, eland_results=8)


def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testLoadRunXML))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
