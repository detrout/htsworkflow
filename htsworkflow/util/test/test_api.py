import copy
import os
from unittest import TestCase

from htsworkflow.util import api

class testApi(TestCase):
    def test_make_key(self):
        k1 = api.make_django_secret_key()
        k2 = api.make_django_secret_key()

        self.assertTrue(len(k1), 85)
        self.assertTrue(len(k2), 85)
        self.assertTrue(k1 != k2)

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestApi))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
