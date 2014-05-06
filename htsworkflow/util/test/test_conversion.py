#!/usr/bin/env python

from unittest import TestCase

from htsworkflow.util import conversion

class TestConversion(TestCase):
    def test_parse_slice(self):
        s = conversion.parse_slice("1:")
        self.failUnlessEqual(s.start, 1)
        self.failUnlessEqual(s.stop, None)

        s = conversion.parse_slice("0:2")
        self.failUnlessEqual(s.start, 0)
        self.failUnlessEqual(s.stop, 2)

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestConversion))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
