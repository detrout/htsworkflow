from unittest2 import TestCase
from htsworkflow.submission.fastqname import FastqName

class TestFastqName(TestCase):
    def test_init_empty(self):
        fq = FastqName()
        self.assertEqual(fq.is_valid, False)

    def test_init_single_filename(self):
        fq = FastqName(filename="12345_AABBCCDDXX_c100_l1.fastq")
        self.assertEqual(fq.lib_id, "12345")
        self.assertEqual(fq['lib_id'], "12345")
        self.assertEqual(fq.flowcell, "AABBCCDDXX")
        self.assertEqual(fq['flowcell'], "AABBCCDDXX")
        self.assertEqual(fq.cycle, "100")
        self.assertEqual(fq['cycle'], "100")
        self.assertEqual(fq.lane, "1")
        self.assertEqual(fq['lane'], "1")
        self.assertEqual(fq.is_paired, False)

    def test_init_single_filename(self):
        fq = FastqName(filename="12345_AABBCCDDXX_c100_l1_r2.fastq")
        self.assertEqual(fq.lib_id, "12345")
        self.assertEqual(fq['lib_id'], "12345")
        self.assertEqual(fq.flowcell, "AABBCCDDXX")
        self.assertEqual(fq['flowcell'], "AABBCCDDXX")
        self.assertEqual(fq.cycle, "100")
        self.assertEqual(fq['cycle'], "100")
        self.assertEqual(fq.lane, "1")
        self.assertEqual(fq['lane'], "1")
        self.assertEqual(fq.read, "2")
        self.assertEqual(fq['read'], "2")
        self.assertEqual(fq.is_paired, True)

    def test_init_bad_filename(self):
        attribs = {'filename': 'asdf.bam'}
        self.assertRaises(ValueError, FastqName, **attribs)

    def test_init_single_attributes(self):
        fq = FastqName(lib_id="12345", flowcell="AABBCCDDXX",
                       cycle = "100", lane="1")
        self.assertEqual(fq.is_valid, True)
        self.assertEqual(fq.lib_id, "12345")
        self.assertEqual(fq['lib_id'], "12345")
        self.assertEqual(fq.flowcell, "AABBCCDDXX")
        self.assertEqual(fq['flowcell'], "AABBCCDDXX")
        self.assertEqual(fq.cycle, "100")
        self.assertEqual(fq['cycle'], "100")
        self.assertEqual(fq.lane, "1")
        self.assertEqual(fq['lane'], "1")
        self.assertEqual(fq.is_paired, False)
        self.assertEqual(fq.filename, "12345_AABBCCDDXX_c100_l1.fastq")

    def test_init_single_attributes_set_single(self):
        fq = FastqName(lib_id="12345", flowcell="AABBCCDDXX",
                       cycle = "100", lane="1", is_paired=False)
        self.assertEqual(fq.is_valid, True)
        self.assertEqual(fq.is_paired, False)

    def test_init_single_attributes_set_paired(self):
        fq = FastqName(lib_id="12345", flowcell="AABBCCDDXX",
                       cycle = "100", lane="1", is_paired=True)
        self.assertEqual(fq.is_valid, False)
        self.assertEqual(fq.is_paired, True)

    def test_init_paired_attributes(self):
        fq = FastqName(lib_id="12345", flowcell="AABBCCDDXX",
                       cycle = "100", lane="1", read="2")
        self.assertEqual(fq.is_valid, True)
        self.assertEqual(fq.lib_id, "12345")
        self.assertEqual(fq['lib_id'], "12345")
        self.assertEqual(fq.flowcell, "AABBCCDDXX")
        self.assertEqual(fq['flowcell'], "AABBCCDDXX")
        self.assertEqual(fq.cycle, "100")
        self.assertEqual(fq['cycle'], "100")
        self.assertEqual(fq.lane, "1")
        self.assertEqual(fq['lane'], "1")
        self.assertEqual(fq.read, "2")
        self.assertEqual(fq['read'], "2")
        self.assertEqual(fq.is_paired, True)
        self.assertEqual(fq.filename, "12345_AABBCCDDXX_c100_l1_r2.fastq")

    def test_init_paired_attributes_set_single(self):
        fq = FastqName(lib_id="12345", flowcell="AABBCCDDXX",
                       cycle = "100", lane="1", read="2", is_paired=False)
        self.assertEqual(fq.is_valid, True)
        self.assertEqual(fq.is_paired, False)

    def test_init_paired_attributes_set_paired(self):
        fq = FastqName(lib_id="12345", flowcell="AABBCCDDXX",
                       cycle = "100", lane="1", read="2", is_paired=True)
        self.assertEqual(fq.is_valid, True)
        self.assertEqual(fq.is_paired, True)

    def test_init_insufficient_attributes(self):
        attribs = dict(lib_id="12345", flowcell="AABBCCDDXX")
        fq = FastqName(**attribs)
        self.assertEqual(fq.is_valid, False)


def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestFastqName))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest='suite')
