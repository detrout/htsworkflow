from __future__ import absolute_import, print_function

from django.test import TestCase

from ..models import FileType, find_file_type_metadata_from_filename

class TestFileType(TestCase):
    def test_file_type_unicode(self):
        file_type_objects = FileType.objects
        name = 'QSEQ tarfile'
        file_type_object = file_type_objects.get(name=name)
        self.assertEqual(u"QSEQ tarfile",
                             unicode(file_type_object))

    def test_find_file_type(self):
        file_type_objects = FileType.objects
        cases = [('woldlab_090921_HWUSI-EAS627_0009_42FC3AAXX_l7_r1.tar.bz2',
                  'QSEQ tarfile', 7, 1),
                 ('woldlab_091005_HWUSI-EAS627_0010_42JT2AAXX_1.srf',
                  'SRF', 1, None),
                 ('s_1_eland_extended.txt.bz2','ELAND Extended', 1, None),
                 ('s_7_eland_multi.txt.bz2', 'ELAND Multi', 7, None),
                 ('s_3_eland_result.txt.bz2','ELAND Result', 3, None),
                 ('s_1_export.txt.bz2','ELAND Export', 1, None),
                 ('s_1_percent_call.png', 'IVC Percent Call', 1, None),
                 ('s_2_percent_base.png', 'IVC Percent Base', 2, None),
                 ('s_3_percent_all.png', 'IVC Percent All', 3, None),
                 ('s_4_call.png', 'IVC Call', 4, None),
                 ('s_5_all.png', 'IVC All', 5, None),
                 ('Summary.htm', 'Summary.htm', None, None),
                 ('run_42JT2AAXX_2009-10-07.xml', 'run_xml', None, None),
         ]
        for filename, typename, lane, end in cases:
            ft = find_file_type_metadata_from_filename(filename)
            self.assertEqual(ft['file_type'],
                                 file_type_objects.get(name=typename))
            self.assertEqual(ft.get('lane', None), lane)
            self.assertEqual(ft.get('end', None), end)

    def test_assign_file_type_complex_path(self):
        file_type_objects = FileType.objects
        cases = [('/a/b/c/woldlab_090921_HWUSI-EAS627_0009_42FC3AAXX_l7_r1.tar.bz2',
                  'QSEQ tarfile', 7, 1),
                 ('foo/woldlab_091005_HWUSI-EAS627_0010_42JT2AAXX_1.srf',
                  'SRF', 1, None),
                 ('../s_1_eland_extended.txt.bz2','ELAND Extended', 1, None),
                 ('/bleem/s_7_eland_multi.txt.bz2', 'ELAND Multi', 7, None),
                 ('/qwer/s_3_eland_result.txt.bz2','ELAND Result', 3, None),
                 ('/ty///1/s_1_export.txt.bz2','ELAND Export', 1, None),
                 ('/help/s_1_percent_call.png', 'IVC Percent Call', 1, None),
                 ('/bored/s_2_percent_base.png', 'IVC Percent Base', 2, None),
                 ('/example1/s_3_percent_all.png', 'IVC Percent All', 3, None),
                 ('amonkey/s_4_call.png', 'IVC Call', 4, None),
                 ('fishie/s_5_all.png', 'IVC All', 5, None),
                 ('/random/Summary.htm', 'Summary.htm', None, None),
                 ('/notrandom/run_42JT2AAXX_2009-10-07.xml', 'run_xml', None, None),
         ]
        for filename, typename, lane, end in cases:
            result = find_file_type_metadata_from_filename(filename)
            self.assertEqual(result['file_type'],
                                 file_type_objects.get(name=typename))
            self.assertEqual(result.get('lane',None), lane)
            self.assertEqual(result.get('end', None), end)

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestFileType))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
