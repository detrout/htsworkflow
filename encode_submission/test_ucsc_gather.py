from unittest2 import TestCase, TestSuite, defaultTestLoader

import ucsc_gather

class testUCSCGather(TestCase):
    pass

def suite():
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testUCSCGather))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest='suite')
