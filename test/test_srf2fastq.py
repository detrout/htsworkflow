import os
from StringIO import StringIO
import sys
import unittest

_module_path, _module_name = os.path.split(__file__)
sys.path.append(os.path.join(_module_path, '..', 'scripts'))

import srf2named_fastq

class testSrf2Fastq(unittest.TestCase):
    def test_split_good(self):
        source = StringIO("""@header
AGCTTTTT
+
IIIIB+++
""")
        target1 = StringIO()
        target2 = StringIO()

        srf2named_fastq.convert_single_to_two_fastq(source, target1, target2)

        target1.seek(0)
        lines1 = target1.readlines()
        self.failUnlessEqual(len(lines1),4)
        self.failUnlessEqual(lines1[0].rstrip(), '@header/1')
        self.failUnlessEqual(lines1[1].rstrip(), 'AGCT')
        self.failUnlessEqual(lines1[2].rstrip(), '+')
        self.failUnlessEqual(lines1[3].rstrip(), 'IIII')

        target2.seek(0)
        lines2 = target2.readlines()
        self.failUnlessEqual(len(lines2),4)
        self.failUnlessEqual(lines2[0].rstrip(), '@header/2')
        self.failUnlessEqual(lines2[1].rstrip(), 'TTTT')
        self.failUnlessEqual(lines2[2].rstrip(), '+')
        self.failUnlessEqual(lines2[3].rstrip(), 'B+++')

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

        srf2named_fastq.convert_single_to_two_fastq(source, target1, target2, header="foo_")

        target1.seek(0)
        lines1 = target1.readlines()
        self.failUnlessEqual(len(lines1),8)
        self.failUnlessEqual(lines1[0].rstrip(), '@foo_header1/1')
        self.failUnlessEqual(lines1[1].rstrip(), 'AGCT')
        self.failUnlessEqual(lines1[2].rstrip(), '+')
        self.failUnlessEqual(lines1[3].rstrip(), '@III')

        target2.seek(0)
        lines2 = target2.readlines()
        self.failUnlessEqual(len(lines2),8)
        self.failUnlessEqual(lines2[0].rstrip(), '@foo_header1/2')
        self.failUnlessEqual(lines2[1].rstrip(), 'TTTT')
        self.failUnlessEqual(lines2[2].rstrip(), '+')
        self.failUnlessEqual(lines2[3].rstrip(), 'B+++')

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

        srf2named_fastq.convert_single_to_fastq(source, target1)

        target1.seek(0)
        lines1 = target1.readlines()
        self.failUnlessEqual(len(lines1),8)
        self.failUnlessEqual(lines1[0].rstrip(), '@header1')
        self.failUnlessEqual(lines1[1].rstrip(), 'AGCTTTTT')
        self.failUnlessEqual(lines1[2].rstrip(), '+')
        self.failUnlessEqual(lines1[3].rstrip(), '@IIIB+++')

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

        srf2named_fastq.convert_single_to_fastq(source, target1, header="foo_")

        target1.seek(0)
        lines1 = target1.readlines()
        self.failUnlessEqual(len(lines1),8)
        self.failUnlessEqual(lines1[0].rstrip(), '@foo_header1')
        self.failUnlessEqual(lines1[1].rstrip(), 'AGCTTTTT')
        self.failUnlessEqual(lines1[2].rstrip(), '+')
        self.failUnlessEqual(lines1[3].rstrip(), '@IIIB+++')


def suite():
    return unittest.makeSuite(testSrf2Fastq,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
