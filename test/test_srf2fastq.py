import os
from six.moves import StringIO
import sys
from unittest import TestCase

_module_path, _module_name = os.path.split(__file__)
sys.path.append(os.path.join(_module_path, '..', 'scripts'))

from htsworkflow.pipelines.test.simulate_runfolder import TESTDATA_DIR

from htsworkflow.pipelines import srf2fastq

class testSrf2Fastq(TestCase):
    def test_split_good(self):
        source = StringIO("""@header
AGCTTTTT
+
IIIIB+++
""")
        target1 = StringIO()
        target2 = StringIO()

        srf2fastq.convert_single_to_two_fastq(source, target1, target2)

        target1.seek(0)
        lines1 = target1.readlines()
        self.assertEqual(len(lines1),4)
        self.assertEqual(lines1[0].rstrip(), '@header/1')
        self.assertEqual(lines1[1].rstrip(), 'AGCT')
        self.assertEqual(lines1[2].rstrip(), '+')
        self.assertEqual(lines1[3].rstrip(), 'IIII')

        target2.seek(0)
        lines2 = target2.readlines()
        self.assertEqual(len(lines2),4)
        self.assertEqual(lines2[0].rstrip(), '@header/2')
        self.assertEqual(lines2[1].rstrip(), 'TTTT')
        self.assertEqual(lines2[2].rstrip(), '+')
        self.assertEqual(lines2[3].rstrip(), 'B+++')

    def test_split_at_with_header(self):
        source = StringIO("""@header1
AGCTTTTT
+
@IIIB+++
@header2
AGCTTTTT
+
IIIIB+++
""")
        target1 = StringIO()
        target2 = StringIO()

        srf2fastq.convert_single_to_two_fastq(source, target1, target2, header="foo_")

        target1.seek(0)
        lines1 = target1.readlines()
        self.assertEqual(len(lines1),8)
        self.assertEqual(lines1[0].rstrip(), '@foo_header1/1')
        self.assertEqual(lines1[1].rstrip(), 'AGCT')
        self.assertEqual(lines1[2].rstrip(), '+')
        self.assertEqual(lines1[3].rstrip(), '@III')

        target2.seek(0)
        lines2 = target2.readlines()
        self.assertEqual(len(lines2),8)
        self.assertEqual(lines2[0].rstrip(), '@foo_header1/2')
        self.assertEqual(lines2[1].rstrip(), 'TTTT')
        self.assertEqual(lines2[2].rstrip(), '+')
        self.assertEqual(lines2[3].rstrip(), 'B+++')

    def test_single_at(self):
        source = StringIO("""@header1
AGCTTTTT
+
@IIIB+++
@header2
AGCTTTTT
+
IIIIB+++
""")
        target1 = StringIO()

        srf2fastq.convert_single_to_fastq(source, target1)

        target1.seek(0)
        lines1 = target1.readlines()
        self.assertEqual(len(lines1),8)
        self.assertEqual(lines1[0].rstrip(), '@header1')
        self.assertEqual(lines1[1].rstrip(), 'AGCTTTTT')
        self.assertEqual(lines1[2].rstrip(), '+')
        self.assertEqual(lines1[3].rstrip(), '@IIIB+++')

    def test_single_at_with_header(self):
        source = StringIO("""@header1
AGCTTTTT
+
@IIIB+++
@header2
AGCTTTTT
+
IIIIB+++
""")
        target1 = StringIO()

        srf2fastq.convert_single_to_fastq(source, target1, header="foo_")

        target1.seek(0)
        lines1 = target1.readlines()
        self.assertEqual(len(lines1),8)
        self.assertEqual(lines1[0].rstrip(), '@foo_header1')
        self.assertEqual(lines1[1].rstrip(), 'AGCTTTTT')
        self.assertEqual(lines1[2].rstrip(), '+')
        self.assertEqual(lines1[3].rstrip(), '@IIIB+++')

    def test_is_srf(self):        
        cnf4_srf = 'woldlab_070829_USI-EAS44_0017_FC11055_1.srf'
        cnf4_path = os.path.join(TESTDATA_DIR, cnf4_srf)
        cnf1_srf = 'woldlab_090512_HWI-EAS229_0114_428NNAAXX_5.srf'
        cnf1_path = os.path.join(TESTDATA_DIR, cnf1_srf)
        
        is_srf = srf2fastq.is_srf
        self.assertEqual(is_srf(__file__), False)
        self.assertEqual(is_srf(cnf4_path), True)
        self.assertEqual(is_srf(cnf1_path), True)

    def test_is_cnf1(self):        
        cnf4_srf = 'woldlab_070829_USI-EAS44_0017_FC11055_1.srf'
        cnf4_path = os.path.join(TESTDATA_DIR, cnf4_srf)
        cnf1_srf = 'woldlab_090512_HWI-EAS229_0114_428NNAAXX_5.srf'
        cnf1_path = os.path.join(TESTDATA_DIR, cnf1_srf)
        
        is_cnf1 = srf2fastq.is_cnf1
        self.failUnlessRaises(ValueError, is_cnf1, __file__)
        self.assertEqual(is_cnf1(cnf4_path), False)
        self.assertEqual(is_cnf1(cnf1_path), True)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testSrf2Fastq))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
