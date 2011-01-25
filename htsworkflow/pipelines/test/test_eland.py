#!/usr/bin/env python
"""More direct synthetic test cases for the eland output file processing
"""
from StringIO import StringIO
import unittest

from htsworkflow.pipelines.eland import ElandLane

class ElandTests(unittest.TestCase):
    """Test specific Eland modules
    """
    def compare_match_array(self, current, expected):
        for key in expected.keys():
            self.failUnlessEqual(current[key], expected[key],
                 "Key %s: %s != %s" % (key,current[key],expected[key]))

    def test_eland_score_mapped_mismatches(self):
        eland = ElandLane()
        match_codes = {'NM':0, 'QC':0, 'RM':0,
                       'U0':0, 'U1':0, 'U2':0,
                       'R0':0, 'R1':0, 'R2':0,
                      }
        r = eland._score_mapped_mismatches("QC", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_QC)
        self.compare_match_array(match_codes, 
                                 {'NM':0, 'QC':1, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })

        r = eland._score_mapped_mismatches("NM", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_QC)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })

        r = eland._score_mapped_mismatches("1:0:0", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':1, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })

        r = eland._score_mapped_mismatches("2:4:16", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':1, 'U1':0, 'U2':0,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("1:1:1", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':2, 'U1':1, 'U2':1,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("1:0:0", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':3, 'U1':1, 'U2':1,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("0:0:1", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':3, 'U1':1, 'U2':2,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("chr3.fa", match_codes)
        self.failUnlessEqual(r, ElandLane.SCORE_UNRECOGNIZED)
        self.compare_match_array(match_codes, 
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':3, 'U1':1, 'U2':2,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })
                                 
    def test_count_mapped_export(self):
        eland = ElandLane()
        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "38")
        self.failUnlessEqual(mapped_reads['chr3.fa'], 1)
        self.failUnlessEqual(r, 'U0')

        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "36A4")
        self.failUnlessEqual(mapped_reads['chr3.fa'], 1)
        self.failUnlessEqual(r, 'U1')

        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "30A2T2")
        self.failUnlessEqual(mapped_reads['chr3.fa'], 1)
        self.failUnlessEqual(r, 'U2')

        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "26AG2T2")
        self.failUnlessEqual(mapped_reads['chr3.fa'], 1)
        self.failUnlessEqual(r, 'U2')

        # deletion
        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "26^AG$4")
        self.failUnlessEqual(mapped_reads['chr3.fa'], 1)
        self.failUnlessEqual(r, 'U2')

        # insertion
        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "26^2$4")
        self.failUnlessEqual(mapped_reads['chr3.fa'], 1)
        self.failUnlessEqual(r, 'U0')

    def test_update_eland_export(self):
        """Test scoring the pipeline export file"""
        eland = ElandLane()
        qc_read = StringIO("ILLUMINA-33A494 1       1       1       3291    1036    0       1       GANNTCCTCACCCGACANNNNNNNANNNCGGGNNACTC  \XBB]^^^^[`````BBBBBBBBBBBBBBBBBBBBBBB  QC")
        one_read_exact = StringIO("ILLUMINA-33A494 1       1       1       2678    1045    0       1       AAGGTGAAGAAGGAGATGNNGATGATGACGACGATAGA  ]]WW[[W]W]]R\WWZ[RBBS^\XVa____]W[]]___  chrX.fa         148341829       F       38       45")
        one_read_mismatch = StringIO("ILLUMINA-33A494 1       1       1       2678    1045    0       1       AAGGTGAAGAAGGAGATGNNGATGATGACGACGATAGA  ]]WW[[W]W]]R\WWZ[RBBS^\XVa____]W[]]___  chrX.fa         148341829       F       18AA15G1T       45")
        multi_read = StringIO("ILLUMINA-33A494 1       1       1       4405    1046    0       1       GTGGTTTCGCTGGATAGTNNGTAGGGACAGTGGGAATC  ``````````__a__V^XBB^SW^^a_____a______  9:2:1")

        match_codes, match_reads, reads = eland._update_eland_export(qc_read)
        self.compare_match_array(match_codes, 
                                 {'NM':0, 'QC':1, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })
        self.failUnlessEqual(len(match_reads), 0)
        self.failUnlessEqual(reads, 1)

        match_codes, match_reads, reads = eland._update_eland_export(one_read_exact)
        self.compare_match_array(match_codes, 
                                 {'NM':0, 'QC':0, 'RM':0,
                                  'U0':1, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })
        self.failUnlessEqual(match_reads['chrX.fa'], 1)
        self.failUnlessEqual(reads, 1)

        match_codes, match_reads, reads = eland._update_eland_export(one_read_mismatch)
        self.compare_match_array(match_codes, 
                                 {'NM':0, 'QC':0, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':1,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })
        self.failUnlessEqual(match_reads['chrX.fa'], 1)
        self.failUnlessEqual(reads, 1)

        match_codes, match_reads, reads = eland._update_eland_export(multi_read)
        self.compare_match_array(match_codes, 
                                 {'NM':0, 'QC':0, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':1,
                                  'R0':9, 'R1':2, 'R2':0,
                                  })
        self.failUnlessEqual(len(match_reads), 0)
        self.failUnlessEqual(reads, 1)


def suite():
    return unittest.makeSuite(ElandTests, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
