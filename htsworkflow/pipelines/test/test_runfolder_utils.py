from unittest2 import TestCase, TestSuite, defaultTestLoader

from htsworkflow.pipelines import runfolder
class TestRunfolderUtilities(TestCase):
    """Some functions can be tested independently of the runfolder version.
    """
    def test_match_aligned_unaligned_abspath(self):
        aligned = ['/a/b/c/Aligned', '/a/b/c/Aligned1234', '/a/b/c/Aligned_3mm']
        unaligned = ['/a/b/c/Unaligned', '/a/b/c/Unaligned_3mm', '/a/b/c/Unaligned_6index']

        matches = set(runfolder.hiseq_match_aligned_unaligned(aligned, unaligned))
        self.assertEqual(len(matches), 4)
        self.assertTrue(('/a/b/c/Aligned', '/a/b/c/Unaligned') in matches )
        self.assertTrue(('/a/b/c/Aligned1234', None) in matches )
        self.assertTrue(('/a/b/c/Aligned_3mm', '/a/b/c/Unaligned_3mm') in matches )
        self.assertTrue((None, '/a/b/c/Unaligned_6index') in matches )

    def test_match_aligned_unaligned_relpath(self):
        aligned = ['./Aligned', './Aligned1234', './Aligned_3mm']
        unaligned = ['./Unaligned', './Unaligned_3mm', './Unaligned_6index']

        matches = set(runfolder.hiseq_match_aligned_unaligned(aligned, unaligned))
        self.assertEqual(len(matches), 4)
        self.assertTrue(('./Aligned', './Unaligned') in matches )
        self.assertTrue(('./Aligned1234', None) in matches )
        self.assertTrue(('./Aligned_3mm', './Unaligned_3mm') in matches )
        self.assertTrue((None, './Unaligned_6index') in matches )

def suite():
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(RunfolderTests))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
