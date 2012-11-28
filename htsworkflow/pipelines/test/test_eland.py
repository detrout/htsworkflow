#!/usr/bin/env python
"""More direct synthetic test cases for the eland output file processing
"""
from StringIO import StringIO
from unittest2 import TestCase

from htsworkflow.pipelines.eland import ELAND, ElandLane, ElandMatches, \
     SampleKey, MatchCodes, MappedReads

class MatchCodeTests(TestCase):
    def test_initializer(self):
        self.assertRaises(ValueError, MatchCodes, {'foo':'bar'})
        self.assertRaises(ValueError, MatchCodes, 3)
        mc = MatchCodes(None)

    def test_dictlike(self):
        mc = MatchCodes()
        match_codes = {'NM':0, 'QC':0, 'RM':0,
                       'U0':0, 'U1':0, 'U2':0,
                       'R0':0, 'R1':0, 'R2':0,
                      }
        self.assertEqual(mc.keys(), match_codes.keys())
        self.assertEqual(mc.items(), match_codes.items())
        self.assertEqual(mc.values(), match_codes.values())
        self.assertRaises(KeyError, mc.__getitem__, 'foo')

    def test_addition(self):
        mc1 = MatchCodes()
        mc2 = MatchCodes({'NM':5, 'QC':10, 'U0': 100})

        mc1['NM'] += 5
        self.assertEqual(mc1['NM'], 5)
        self.assertEqual(mc1['QC'], 0)
        self.assertEqual(mc1['U0'], 0)
        mc1 += mc2
        self.assertEqual(mc1['NM'], 10)
        self.assertEqual(mc1['QC'], 10)
        self.assertEqual(mc1['U0'], 100)


class TestMappedReads(TestCase):
    def test_initializer(self):
        mr1 = MappedReads()
        self.assertEqual(len(mr1), 0)
        mr2 = MappedReads({'hg19': 100, 'newcontamUK.fa': 12})
        self.assertEqual(len(mr2), 2)
        self.assertEqual(mr2['hg19'], 100)

        self.assertRaises(ValueError, MappedReads, 3)

    def test_dictionaryness(self):
        mr1 = MappedReads()
        mr1['chr9'] = 7
        self.assertEqual(list(mr1.keys()), ['chr9'])
        self.assertEqual(mr1['chr9'], 7)
        self.assertEqual(mr1.items(), [('chr9', 7)])
        del mr1['chr9']
        self.assertEqual(len(mr1), 0)

    def test_addition(self):
        mr1 = MappedReads({'hg19': 100, 'Lambda1': 5})
        mr2 = MappedReads({'hg19': 100, 'newcontamUK.fa': 10})
        mr3 = mr1 + mr2

        self.assertEqual(len(mr1), 2)
        self.assertEqual(len(mr2), 2)
        self.assertEqual(len(mr3), 3)

        self.assertEqual(mr1['Lambda1'], 5)
        self.assertRaises(KeyError, mr1.__getitem__, 'newcontamUK.fa')
        self.assertEqual(mr1.get('newcontamUK.fa', None), None)

        mr3['Lambda3'] = 2
        self.assertEqual(mr3['Lambda3'], 2)

class ElandTests(TestCase):
    """Test specific Eland modules
    """
    def compare_match_array(self, current, expected):
        for key in expected.keys():
            self.assertEqual(current[key], expected[key],
                 "Key %s: %s != %s" % (key,current[key],expected[key]))

    def test_eland_score_mapped_mismatches(self):
        eland = ElandLane()
        match_codes = {'NM':0, 'QC':0, 'RM':0,
                       'U0':0, 'U1':0, 'U2':0,
                       'R0':0, 'R1':0, 'R2':0,
                      }
        r = eland._score_mapped_mismatches("QC", match_codes)
        self.assertEqual(r, ElandLane.SCORE_QC)
        self.compare_match_array(match_codes,
                                 {'NM':0, 'QC':1, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })

        r = eland._score_mapped_mismatches("NM", match_codes)
        self.assertEqual(r, ElandLane.SCORE_QC)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })

        r = eland._score_mapped_mismatches("1:0:0", match_codes)
        self.assertEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':1, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })

        r = eland._score_mapped_mismatches("2:4:16", match_codes)
        self.assertEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':1, 'U1':0, 'U2':0,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("1:1:1", match_codes)
        self.assertEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':2, 'U1':1, 'U2':1,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("1:0:0", match_codes)
        self.assertEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':3, 'U1':1, 'U2':1,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("0:0:1", match_codes)
        self.assertEqual(r, ElandLane.SCORE_READ)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':3, 'U1':1, 'U2':2,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

        r = eland._score_mapped_mismatches("chr3.fa", match_codes)
        self.assertEqual(r, ElandLane.SCORE_UNRECOGNIZED)
        self.compare_match_array(match_codes,
                                 {'NM':1, 'QC':1, 'RM':0,
                                  'U0':3, 'U1':1, 'U2':2,
                                  'R0':2, 'R1':4, 'R2':16,
                                  })

    def test_count_mapped_export(self):
        eland = ElandLane()
        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "38")
        self.assertEqual(mapped_reads['chr3.fa'], 1)
        self.assertEqual(r, 'U0')

        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "36A4")
        self.assertEqual(mapped_reads['chr3.fa'], 1)
        self.assertEqual(r, 'U1')

        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "30A2T2")
        self.assertEqual(mapped_reads['chr3.fa'], 1)
        self.assertEqual(r, 'U2')

        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "26AG2T2")
        self.assertEqual(mapped_reads['chr3.fa'], 1)
        self.assertEqual(r, 'U2')

        # deletion
        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "26^AG$4")
        self.assertEqual(mapped_reads['chr3.fa'], 1)
        self.assertEqual(r, 'U2')

        # insertion
        mapped_reads = {}
        r = eland._count_mapped_export(mapped_reads, "chr3.fa", "26^2$4")
        self.assertEqual(mapped_reads['chr3.fa'], 1)
        self.assertEqual(r, 'U0')

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
        self.assertEqual(len(match_reads), 0)
        self.assertEqual(reads, 1)

        match_codes, match_reads, reads = eland._update_eland_export(one_read_exact)
        self.compare_match_array(match_codes,
                                 {'NM':0, 'QC':0, 'RM':0,
                                  'U0':1, 'U1':0, 'U2':0,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })
        self.assertEqual(match_reads['chrX.fa'], 1)
        self.assertEqual(reads, 1)

        match_codes, match_reads, reads = eland._update_eland_export(one_read_mismatch)
        self.compare_match_array(match_codes,
                                 {'NM':0, 'QC':0, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':1,
                                  'R0':0, 'R1':0, 'R2':0,
                                  })
        self.assertEqual(match_reads['chrX.fa'], 1)
        self.assertEqual(reads, 1)

        match_codes, match_reads, reads = eland._update_eland_export(multi_read)
        self.compare_match_array(match_codes,
                                 {'NM':0, 'QC':0, 'RM':0,
                                  'U0':0, 'U1':0, 'U2':1,
                                  'R0':9, 'R1':2, 'R2':0,
                                  })
        self.assertEqual(len(match_reads), 0)
        self.assertEqual(reads, 1)

    def test_ordering(self):
        e = ELAND()
        sl3 = SampleKey(lane=3, read=1, sample='33333')
        sl1 = SampleKey(lane=1, read=1, sample='11111')
        sl5 = SampleKey(lane=5, read=1, sample='55555')
        e.results[sl5] = 'Lane5'
        e.results[sl3] = 'Lane3'
        e.results[sl1] = 'Lane1'

        e_list = e.values()
        print e.items()
        self.assertEqual(e_list[0], 'Lane1')
        self.assertEqual(e_list[1], 'Lane3')
        self.assertEqual(e_list[2], 'Lane5')

class TestElandMatches(TestCase):
    def test_eland_replacing(self):
        key = SampleKey(1, 1, 's')
        e = ELAND()
        em = ElandMatches(e)
        em.add('s_1_sequence.txt')
        self.assertEqual(len(em), 1)
        self.assertEqual(len(em[key]), 1)
        filename = iter(em[key]).next().filename
        self.assertEqual(filename, 's_1_sequence.txt')
        self.assertEqual(em.keys(), [key])
        em.add('s_1_eland_result.txt')
        self.assertEqual(len(em), 1)
        self.assertEqual(len(em[key]), 1)
        filename = iter(em[key]).next().filename
        self.assertEqual(filename, 's_1_eland_result.txt')
        self.assertEqual(em.keys(), [key])

    def test_parts(self):
        key11111 = SampleKey(1, 1, '11111')
        key11112 = SampleKey(1, 1, '11112')
        e = ELAND()
        em = ElandMatches(e)
        em.add('11111_CCAATT_L001_R1_001_export.txt.gz')
        em.add('11111_CCAATT_L001_R1_002_export.txt.gz')
        em.add('11111_CCAATT_L001_R1_003_export.txt.gz')
        em.add('11112_AAGGTT_L001_R1_001_export.txt.gz')
        em.add('11112_AAGGTT_L001_R1_002_export.txt.gz')
        self.assertEqual(len(em), 2)
        self.assertEqual(len(em[key11111]), 3)
        self.assertEqual(len(em[key11112]), 2)

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(MatchCodeTests))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestMappedReads))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(ElandTests))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestElandMatches))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
