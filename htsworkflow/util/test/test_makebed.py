import os
from six.moves import StringIO
from unittest import TestCase

from htsworkflow.util import makebed

class testMakeBed(TestCase):
    def test_multi_1_0_0_limit_1(self):
      instream = StringIO('>HWI-EAS229_26_209LVAAXX:7:3:112:383    TCAAATCTTATGCTANGAATCNCAAATTTTCT 1:0:0   mm9_chr13_random.fa:1240R0')
      out = StringIO()

      out = list(makebed.make_bed_from_multi_eland_generator(instream, 'name', 'description', 'mm9_chr', 1))
      self.failUnlessEqual(out[1], 'mm9_chr13_random 1240 1272 read 0 - - - 255,255,0\n')

    def test_multi_1_0_0_limit_255(self):
      instream = StringIO('>HWI-EAS229_26_209LVAAXX:7:3:112:383    TCAAATCTTATGCTANGAATCNCAAATTTTCT 1:0:0   mm9_chr13_random.fa:1240R0')
      out = StringIO()

      out = list(makebed.make_bed_from_multi_eland_generator(instream, 'name', 'desc', 'mm9_chr', 255))
      self.failUnlessEqual(out[1], 'mm9_chr13_random 1240 1272 read 0 - - - 255,255,0\n')


    def test_multi_2_0_0_limit_1(self):
      instream = StringIO('>HWI-EAS229_26_209LVAAXX:7:3:104:586    GTTCTCGCATAAACTNACTCTNAATAGATTCA 2:0:0   mm9_chr4.fa:42995432F0,mm9_chrX.fa:101541458F0')
      out = StringIO()

      out = list(makebed.make_bed_from_multi_eland_generator(instream, 'name', 'desc', 'mm9_chr', 1))
      self.failUnlessEqual(len(out), 1)

    def test_multi_2_0_0_limit_255(self):
      instream = StringIO('>HWI-EAS229_26_209LVAAXX:7:3:104:586    GTTCTCGCATAAACTNACTCTNAATAGATTCA 2:0:0   mm9_chr4.fa:42995432F0,mm9_chrX.fa:101541458F0')
      out = StringIO()

      out = list(makebed.make_bed_from_multi_eland_generator(instream, 'name', 'desc', 'mm9_chr', 255))
      self.failUnlessEqual(len(out), 3)
      self.failUnlessEqual(out[1], 
        'mm9_chr4 42995432 42995464 read 0 + - - 0,0,255\n')
      self.failUnlessEqual(out[2], 
        'mm9_chrX 101541458 101541490 read 0 + - - 0,0,255\n')

    def test_multi_0_2_0_limit_1(self):
      instream = StringIO('>HWI-EAS229_26_209LVAAXX:7:3:115:495    TCTCCCTGAAAAATANAAGTGNTGTTGGTGAG        0:2:1   mm9_chr14.fa:104434729F2,mm9_chr16.fa:63263818R1,mm9_chr2.fa:52265438R1')
      out = StringIO()

      out = list(makebed.make_bed_from_multi_eland_generator(instream, 'name', 'desc', 'mm9_chr', 1))
      self.failUnlessEqual(len(out), 1)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testMakeBed))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
