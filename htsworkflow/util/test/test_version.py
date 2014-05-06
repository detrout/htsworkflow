from unittest import TestCase

from htsworkflow.util import version

class TestVersion(TestCase):
    def test_version(self):
        long_version = version.version()
        self.assertTrue(long_version)
        self.assertEqual(long_version.project_name, 'htsworkflow')
        self.assertTrue(long_version.version)
        

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTest(defaultTestLoader.loadTestsFromTestCase(TestVersion))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
