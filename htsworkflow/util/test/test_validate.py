import os
from six.moves import StringIO
from unittest import TestCase

from htsworkflow.util import validate

class TestValidate(TestCase):
    def test_phred33_works(self):
        q = StringIO(u"@ abc\nAGCT\n+\nBBBB\n")
        errors = validate.validate_fastq(q)
        self.assertEqual(0, errors)

    def test_phred64_works(self):
        q = StringIO(u"@ abc\nAGCT\n+\nfgh]\n")
        errors = validate.validate_fastq(q, 'phred64')
        self.assertEqual(0, errors)

    def test_fasta_fails(self):
        q = StringIO(u">abc\nAGCT\n>foo\nCGAT\n")
        errors = validate.validate_fastq(q)
        self.assertEqual(3, errors)

    def test_fastq_diff_length_uniform(self):
        q = StringIO(u"@ abc\nAGCT\n+\nBBBB\n@ abcd\nAGCTT\n+\nJJJJJ\n")
        errors = validate.validate_fastq(q, 'phred33', True)
        self.assertEqual(2, errors)

    def test_fastq_diff_length_variable(self):
        q = StringIO(u"@ abc\nAGCT\n+\n@@@@\n@ abcd\nAGCTT\n+\nJJJJJ\n")
        errors = validate.validate_fastq(q, 'phred33', False)
        self.assertEqual(0, errors)

    def test_fastq_qual_short(self):
        q = StringIO(u"@ abc\nAGCT\n+\nJJ\n")
        errors = validate.validate_fastq(q)
        self.assertEqual(1, errors)

    def test_fastq_seq_invalid_char(self):
        q = StringIO(u"@ abc\nAGC\u1310\n+\nEFGH\n")
        errors = validate.validate_fastq(q)
        self.assertEqual(1, errors)

    def test_fastq_qual_invalid_char(self):
        q = StringIO(u"+ abc\nAGC.\n+\n!@#J\n")
        errors = validate.validate_fastq(q)
        self.assertEqual(1, errors)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testValidate))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
