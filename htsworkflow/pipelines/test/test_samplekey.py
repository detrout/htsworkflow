#!/usr/bin/env python
"""More direct synthetic test cases for the eland output file processing
"""
from StringIO import StringIO
from unittest2 import TestCase

from htsworkflow.pipelines.samplekey import SampleKey

class TestSampleKey(TestCase):
    def test_equality(self):
        k1 = SampleKey(lane=1, read='1', sample='12345')
        k2 = SampleKey(lane=1, read=1, sample='12345')
        k3 = SampleKey(lane=1, read=2, sample='12345')

        self.assertEqual(k1, k2)
        self.assertEqual(hash(k1), hash(k2))
        self.assertNotEqual(k1, k3)

        self.assertTrue(k1 < k3)
        self.assertTrue(k1 <= k2)

        self.assertTrue(k3 > k1)


    def test_matching(self):
        k1 = SampleKey(lane=1, read='1', sample='12345')
        k2 = SampleKey(lane=1, read=1, sample='12345')
        k3 = SampleKey(lane=1, read=2, sample='12345')

        q1 = SampleKey()
        q2 = SampleKey(read=1)
        q3 = SampleKey(sample='12345')

        self.assertTrue(k1.matches(q1))
        self.assertTrue(k2.matches(q1))
        self.assertTrue(k3.matches(q1))

        self.assertTrue(k1.matches(q2))
        self.assertTrue(k2.matches(q2))
        self.assertFalse(k3.matches(q2))

        self.assertTrue(k1.matches(q3))
        self.assertTrue(k2.matches(q3))
        self.assertTrue(k3.matches(q3))

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestSampleKey))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
