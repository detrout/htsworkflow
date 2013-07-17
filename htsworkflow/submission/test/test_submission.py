import os
from StringIO import StringIO
import shutil
import tempfile
from unittest2 import TestCase, TestSuite, defaultTestLoader

from htsworkflow.submission import daf, results
from htsworkflow.util.rdfhelp import \
     dafTermOntology, \
     fromTypedNode, \
     load_string_into_model, \
     rdfNS, \
     submissionLog, \
     submissionOntology, \
     get_model, \
     get_serializer
from htsworkflow.submission.submission import list_submissions
import RDF

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

def suite():
    suite = TestSuite()
    suite.addTests(
        defaultTestLoader.loadTestsFromTestCase(TestSubmissionModule))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest='suite')
