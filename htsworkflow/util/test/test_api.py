import copy
import os
import unittest

from htsworkflow.util import api

class testApi(unittest.TestCase):
    def test_make_key(self):
        k1 = api.make_django_secret_key()
        k2 = api.make_django_secret_key()

        self.failUnless(len(k1), 85)
        self.failUnless(len(k2), 85)
        self.failUnless(k1 != k2)

def suite():
    return unittest.makeSuite(testApi, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
