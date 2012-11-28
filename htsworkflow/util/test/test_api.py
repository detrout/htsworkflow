import copy
import os
from unittest2 import TestCase

from htsworkflow.util import api

class testApi(TestCase):
    def test_make_key(self):
        k1 = api.make_django_secret_key()
        k2 = api.make_django_secret_key()

        self.failUnless(len(k1), 85)
        self.failUnless(len(k2), 85)
        self.failUnless(k1 != k2)

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestApi))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
