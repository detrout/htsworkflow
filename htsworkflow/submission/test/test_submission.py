
import os
from StringIO import StringIO
import shutil
import tempfile
from unittest import TestCase, TestSuite, defaultTestLoader

from htsworkflow.submission import daf, results
from htsworkflow.util.rdfhelp import \
     dafTermOntology, \
     dump_model, \
     fromTypedNode, \
     get_turtle_header, \
     load_string_into_model, \
     rdfNS, \
     submissionLog, \
     submissionOntology, \
     get_model, \
     get_serializer
from htsworkflow.submission.submission import list_submissions, Submission
from htsworkflow.submission.results import ResultMap
from submission_test_common import *

import RDF
#import logging
#logging.basicConfig(level=logging.DEBUG)

class TestSubmissionModule(TestCase):
    def test_empty_list_submission(self):
        model = get_model()
        self.assertEqual(len(list(list_submissions(model))), 0)

    def test_one_submission(self):
        model = get_model()
        load_string_into_model(model, "turtle",
            """
            @prefix subns: <http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#> .
            @prefix test: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test#> .

            <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test#>
               subns:has_submission test:lib1 ;
               subns:has_submission test:lib2.
            """)
        submissions = list(list_submissions(model))
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0], "test")

    def test_two_submission(self):
        model = get_model()
        load_string_into_model(model, "turtle",
            """
            @prefix subns: <http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#> .
            @prefix test: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test#> .

            <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test1#>
               subns:has_submission test:lib1 .
            <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test2#>
               subns:has_submission test:lib2 .
            """)
        submissions = list(list_submissions(model))
        self.assertEqual(len(submissions), 2)
        truth = set(["test1", "test2"])
        testset = set()
        for name in submissions:
            testset.add(name)
        self.assertEqual(testset, truth)

class TestSubmission(TestCase):
    def setUp(self):
        generate_sample_results_tree(self, 'submission_test')
        self.model = get_model()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_create_submission(self):
        model = get_model()
        s = Submission('foo', self.model, 'http://localhost')
        self.assertEqual(str(s.submissionSet),
                         "http://jumpgate.caltech.edu/wiki/SubmissionsLog/foo")
        self.assertEqual(str(s.submissionSetNS['']),
                         str(RDF.NS(str(s.submissionSet) + '#')['']))
        self.assertEqual(str(s.libraryNS['']),
                         str(RDF.NS('http://localhost/library/')['']))

    def test_scan_submission_dirs(self):
        turtle = get_turtle_header() + """
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test/view/> .
thisView:Fastq ucscDaf:filename_re ".*[^12]\\.fastq\\.bz2$" ;
               a geoSoft:raw ;
               geoSoft:fileTypeLabel "fastq" ;
               ucscDaf:output_type "read" .
thisView:FastqRead1 ucscDaf:filename_re ".*r1\\.fastq\\.bz2$" ;
               a geoSoft:raw ;
               geoSoft:fileTypeLabel "fastq" ;
               ucscDaf:output_type "read1" .
thisView:FastqRead2 ucscDaf:filename_re ".*r2\\.fastq\\.bz2$" ;
               a geoSoft:raw ;
               geoSoft:fileTypeLabel "fastq" ;
               ucscDaf:output_type "read2" .
thisView:alignments ucscDaf:filename_re ".*\\.bam$" ;
               a geoSoft:supplemental ;
               geoSoft:fileTypeLabel "bam" ;
               ucscDaf:output_type "alignments" .

        """
        map = ResultMap()
        map['1000'] = os.path.join(self.sourcedir, S1_NAME)
        map['2000'] = os.path.join(self.sourcedir, S2_NAME)

        s = Submission('foo', self.model, 'http://localhost')
        mock = MockAddDetails(self.model, turtle)
        mock.add_turtle(S1_TURTLE)
        mock.add_turtle(S2_TURTLE)
        s._add_library_details_to_model =  mock
        s.scan_submission_dirs(map)

        nodes = list(s.analysis_nodes(map))
        self.assertEqual(len(nodes), 2)
        expected = set((
            'http://jumpgate.caltech.edu/wiki/SubmissionsLog/foo#1000-sample',
            'http://jumpgate.caltech.edu/wiki/SubmissionsLog/foo#2000-sample',
        ))
        got = set((str(nodes[0]), str(nodes[1])))
        self.assertEqual(expected, got)

    def test_find_best_match(self):
        turtle = get_turtle_header() + """
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/test/view/> .
thisView:Fastq ucscDaf:filename_re ".*[^12]\\.fastq\\.bz2$" ;
               a geoSoft:raw ;
               geoSoft:fileTypeLabel "fastq" ;
               ucscDaf:output_type "read" .
thisView:FastqRead1 ucscDaf:filename_re ".*r1\\.fastq\\.bz2$" ;
               a geoSoft:raw ;
               geoSoft:fileTypeLabel "fastq" ;
               ucscDaf:output_type "read1" .
thisView:FastqRead2 ucscDaf:filename_re ".*r2\\.fastq\\.bz2$" ;
               a geoSoft:raw ;
               geoSoft:fileTypeLabel "fastq" ;
               ucscDaf:output_type "read2" .
thisView:alignments ucscDaf:filename_re ".*\\.bam$" ;
               a geoSoft:supplemental ;
               geoSoft:fileTypeLabel "bam" ;
               ucscDaf:output_type "alignments" .

        """
        load_string_into_model(self.model, 'turtle', turtle)
        s = Submission('foo', self.model, 'http://localhost')
        q = RDF.Statement(None, dafTermOntology['filename_re'], None)
        view_map = s._get_filename_view_map()
        self.assertEqual(len(view_map), 4)

        fastq = s.find_best_match("asdf.fastq.bz2")
        self.assertEqual(
            str(fastq),
            "http://jumpgate.caltech.edu/wiki/SubmissionsLog/test/view/Fastq")

        fastq = s.find_best_match("asdf.r2.fastq.bz2")
        self.assertEqual(
            str(fastq),
            "http://jumpgate.caltech.edu/wiki/SubmissionsLog/test/view/FastqRead2")

def suite():
    suite = TestSuite()
    suite.addTests(
        defaultTestLoader.loadTestsFromTestCase(TestSubmissionModule))
    suite.addTests(
        defaultTestLoader.loadTestsFromTestCase(TestSubmission))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest='suite')
