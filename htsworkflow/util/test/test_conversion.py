#!/usr/bin/env python

from unittest import TestCase

from htsworkflow.util import conversion

class TestConversion(TestCase):
    def test_parse_slice(self):
        s = conversion.parse_slice("1:")
        self.assertEqual(s.start, 1)
        self.assertEqual(s.stop, None)

        s = conversion.parse_slice("0:2")
        self.assertEqual(s.start, 0)
        self.assertEqual(s.stop, 2)

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestConversion))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
