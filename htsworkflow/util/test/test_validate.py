import os
from StringIO import StringIO
import unittest

from htsworkflow.util import validate

class TestValidate(unittest.TestCase):
    def test_fastq_works(self):
        q = StringIO(u"> abc\nAGCT\n@\nBBBB\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(0, errors)

    def test_fastq_diff_length_uniform(self):
        q = StringIO(u"> abc\nAGCT\n@\nBBBB\n> abcd\nAGCTT\n@\nJJJJJ\n")
        errors = validate.validate_fastq(q, True)
        self.failUnlessEqual(2, errors)

    def test_fastq_diff_length_variable(self):
        q = StringIO(u"> abc\nAGCT\n@\n@@@@\n> abcd\nAGCTT\n@\nJJJJJ\n")
        errors = validate.validate_fastq(q, False)
        self.failUnlessEqual(0, errors)

    def test_fastq_qual_short(self):
        q = StringIO(u"> abc\nAGCT\n@\nSS\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(1, errors)

    def test_fastq_seq_invalid_char(self):
        q = StringIO(u"> abc\nAGC\u1310\n@\nPQRS\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(1, errors)

    def test_fastq_qual_invalid_char(self):
        q = StringIO(u"> abc\nAGC.\n@\n!@#J\n")
        errors = validate.validate_fastq(q)
        self.failUnlessEqual(1, errors)

def suite():
    return unittest.makeSuite(testValidate, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')


