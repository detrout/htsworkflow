import os
from StringIO import StringIO
import unittest

from htsworkflow.util import validate

class TestValidate(unittest.TestCase):
    def test_phred33_works(self):
        q = StringIO(u"@ abc\nAGCT\n+\nBBBB\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(0, errors)

    def test_phred64_works(self):
        q = StringIO(u"@ abc\nAGCT\n+\nfgh]\n")
        errors = validate.validate_fastq(q, 'phred64')
        self.failUnlessEqual(0, errors)

    def test_fasta_fails(self):
        q = StringIO(u">abc\nAGCT\n>foo\nCGAT\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(3, errors)

    def test_fastq_diff_length_uniform(self):
        q = StringIO(u"@ abc\nAGCT\n+\nBBBB\n@ abcd\nAGCTT\n+\nJJJJJ\n")
        errors = validate.validate_fastq(q, 'phred33', True)
        self.failUnlessEqual(2, errors)

    def test_fastq_diff_length_variable(self):
        q = StringIO(u"@ abc\nAGCT\n+\n@@@@\n@ abcd\nAGCTT\n+\nJJJJJ\n")
        errors = validate.validate_fastq(q, 'phred33', False)
        self.failUnlessEqual(0, errors)

    def test_fastq_qual_short(self):
        q = StringIO(u"@ abc\nAGCT\n+\nJJ\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(1, errors)

    def test_fastq_seq_invalid_char(self):
        q = StringIO(u"@ abc\nAGC\u1310\n+\nEFGH\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(1, errors)

    def test_fastq_qual_invalid_char(self):
        q = StringIO(u"+ abc\nAGC.\n+\n!@#J\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(1, errors)

def suite():
    return unittest.makeSuite(testValidate, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')


