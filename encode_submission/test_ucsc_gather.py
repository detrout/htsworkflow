from __future__ import absolute_import

from unittest import TestCase, TestSuite, defaultTestLoader

from . import ucsc_gather

class testUCSCGather(TestCase):
    pass

def suite():
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testUCSCGather))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest='suite')
