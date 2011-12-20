#!/usr/bin/env python
import os
import unittest

import RDF

import encode_find
from htsworkflow.submission.ucsc import submission_view_url
from htsworkflow.util.rdfhelp import dump_model, get_model

SOURCE_PATH = os.path.split(os.path.abspath(__file__))[0]
print SOURCE_PATH

class TestEncodeFind(unittest.TestCase):
    def test_create_status_node_with_uri(self):
        subURL = submission_view_url('5136')
        submissionUri = RDF.Uri(subURL)
        timestamp = '2011-12-19T12:42:53.048956'
        manualUri = subURL + '/' + timestamp
        nodeUri = encode_find.create_status_node(submissionUri, timestamp)
        self.assertEqual(str(nodeUri.uri), manualUri)

    def test_create_status_node_with_str(self):
        subURL = submission_view_url('5136')
        timestamp = '2011-12-19T12:42:53.048956'
        manualUri = subURL + '/' + timestamp
        nodeUri = encode_find.create_status_node(subURL, timestamp)
        self.assertEqual(str(nodeUri.uri), manualUri)

    def test_parse_submission_page(self):
        timestamp = '2011-12-19T12:42:53.048956'
        subURL = submission_view_url('5136')
        subNode = encode_find.create_status_node(subURL, timestamp)
        test_file = os.path.join(SOURCE_PATH, 'testdata', '5136SubDetail.html')
        from lxml.html import parse
        tree = parse(test_file)
        model = get_model()
        dates = encode_find.get_creation_dates(model, subNode)
        self.assertEqual(len(dates), 0)
        encode_find.parse_submission_page(model, tree, subNode)
        dates = encode_find.get_creation_dates(model, subNode)
        self.assertEqual(len(dates), 1)
        self.assertEqual(str(dates[0].object), '2011-12-07T15:23:00')

def suite():
    return unittest.makeSuite(TestEncodeFind, "test")

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
