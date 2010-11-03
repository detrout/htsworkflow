import unittest

import ucsc_gather

class testUCSCGather(unittest.TestCase):
    def test_view_attribute_map(self):
        view_map = ucsc_gather.NameToViewMap()
        view_map.lib_cache["0"] = {
            "cell_line": "NLHF",
            "replicate": "1",
            "lane_set": {},
            }
    
        a = view_map.find_attributes("foo.ini", "0")    
        self.failUnless(a["view"] is None)
    
        a = view_map.find_attributes("asdf.fdsa", "0")
        self.failUnless(a is None)
    
        a = view_map.find_attributes("foo.fastq", "0")
        self.failUnlessEqual(a["view"], "Fastq", "0")
    
        a = view_map.find_attributes("foo_r1.fastq", "0")
        self.failUnlessEqual(a["view"], "FastqRd1", "0")

    def test_get_library_info_paired(self):
        view_map = ucsc_gather.NameToViewMap()
        view_map.lib_cache["11588"] = {
            u'antibody_id': None,
            u'cell_line': u'NHLF',
            u'cell_line_id': 13,
            u'experiment_type': u'RNA-seq',
            u'experiment_type_id': 4,
            u'gel_cut_size': 300,
            u'hidden': False,
            u'id': u'11588',
            u'insert_size': 200,
            u'lane_set': [{u'flowcell': u'61PKCAAXX',
                           u'lane_number': 8,
                           u'paired_end': True,
                           u'read_length': 76,
                           u'status': u'Unknown',
                           u'status_code': None},
                          {u'flowcell': u'61PKLAAXX',
                           u'lane_number': 8,
                           u'paired_end': True,
                           u'read_length': 76,
                           u'status': u'Unknown',
                           u'status_code': None}],
            u'library_id': u'11588',
            u'library_name': u'Paired ends 254 NHLF 31',
            u'library_species': u'Homo sapiens',
            u'library_species_id': 8,
            u'library_type': u'Paired End',
            u'library_type_id': 2,
            u'made_by': u'Brian',
            u'made_for': u'Brian',
            u'notes': u'300 bp gel fragment, SPRI beads cleanup',
            u'replicate': 2,
            u'stopping_point': u'1Aa',
            u'successful_pM': None,
            u'undiluted_concentration': u'26.2'}

        a = view_map.find_attributes("foo.bam", "11588")
        self.failUnlessEqual(a["view"], "Paired")
        self.failUnlessEqual(a["insertLength"], 200)


def suite():
    return unittest.makeSuite(testUCSCGather,"test")

if __name__ == "__main__":
    unittest.main(defaultTest="suite")

