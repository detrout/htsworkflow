#!/usr/bin/env python

import unittest

from htsworkflow.util import conversion

class TestConversion(unittest.TestCase):
    def test_parse_slice(self):
        s = conversion.parse_slice("1:")
        self.failUnlessEqual(s.start, 1)
        self.failUnlessEqual(s.stop, None)

        s = conversion.parse_slice("0:2")
        self.failUnlessEqual(s.start, 0)
        self.failUnlessEqual(s.stop, 2)

def suite():
    return unittest.makeSuite(TestConversion, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")

