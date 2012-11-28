#!/usr/bin/env python
from datetime import datetime
import os
from unittest2 import TestCase

import RDF

import encode_find
from htsworkflow.submission.ucsc import submission_view_url
from htsworkflow.util.rdfhelp import add_default_schemas, \
     dump_model, get_model, fromTypedNode
from htsworkflow.util.rdfinfer import Infer

SOURCE_PATH = os.path.split(os.path.abspath(__file__))[0]
print SOURCE_PATH

class TestEncodeFind(TestCase):
    def setUp(self):
        self.model = get_model()
        add_default_schemas(self.model)
        self.inference = Infer(self.model)

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
        dates = encode_find.get_creation_dates(self.model, subNode)
        self.assertEqual(len(dates), 0)
        encode_find.parse_submission_page(self.model, tree, subNode)
        dates = encode_find.get_creation_dates(self.model, subNode)
        self.assertEqual(len(dates), 1)
        object_date = fromTypedNode(dates[0].object)
        self.assertEqual(object_date, datetime(2011,12,7,15,23,0))

    def test_delete_simple_lane(self):
        model = get_model()
        parser = RDF.Parser(name='turtle')
        parser.parse_string_into_model(model, '''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix : <http://www.w3.org/1999/xhtml> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#> .

<http://jumpgate.caltech.edu/lane/1232>
    libns:flowcell <http://jumpgate.caltech.edu/flowcell/42JV5AAXX/> ;
    libns:total_unique_locations 5789938 .

''', 'http://jumpgate.caltech.edu/library/')
        errmsgs = list(self.inference.run_validation())
        self.assertEqual(len(errmsgs), 0)
        urn = RDF.Node(RDF.Uri('http://jumpgate.caltech.edu/lane/1232'))
        encode_find.delete_lane(model, urn)
        self.failUnlessEqual(len(model), 0)

    def test_delete_lane_with_mapping(self):
        ontology_size = len(self.model)
        parser = RDF.Parser(name='turtle')
        parser.parse_string_into_model(self.model, '''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix : <http://www.w3.org/1999/xhtml> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#> .

<http://jumpgate.caltech.edu/flowcell/42JV5AAXX/> a libns:IlluminaFlowcell .
<http://jumpgate.caltech.edu/lane/1232>
    libns:flowcell <http://jumpgate.caltech.edu/flowcell/42JV5AAXX/> ;
    libns:has_mappings _:bnode110110 ;
    libns:total_unique_locations 5789938 ;
    a libns:IlluminaLane .

_:bnode110110
    a libns:MappedCount ;
    libns:mapped_to "newcontam_UK.fa"@en ;
    libns:reads 42473 .
''', 'http://jumpgate.caltech.edu/library/')
        errmsgs = list(self.inference.run_validation())
        self.assertEqual(len(errmsgs), 0)
        self.failUnlessEqual(len(self.model), 8 + ontology_size)
        urn = RDF.Node(RDF.Uri('http://jumpgate.caltech.edu/lane/1232'))
        encode_find.delete_lane(self.model, urn)
        self.failUnlessEqual(len(self.model), 1 + ontology_size)
        # the flowcell triple wasn't deleted.

    def test_delete_library(self):
        parser = RDF.Parser(name='turtle')
        parser.parse_string_into_model(self.model, '''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix : <http://www.w3.org/1999/xhtml> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#> .

<http://jumpgate.caltech.edu/flowcell/42JV5AAXX/> a libns:IlluminaFlowcell .
<http://jumpgate.caltech.edu/flowcell/62WCKAAXX/> a libns:IlluminaFlowcell .

<http://jumpgate.caltech.edu/lane/1232>
    a libns:IlluminaLane ;
    libns:flowcell <http://jumpgate.caltech.edu/flowcell/42JV5AAXX/> ;
    libns:has_mappings _:bnode110110 ;
    libns:total_unique_locations 5789938 .

<http://jumpgate.caltech.edu/library/11011/>
    libns:affiliation "ENCODE"@en, "ENCODE_Tier1"@en, "Georgi Marinov"@en ;
    libns:has_lane <http://jumpgate.caltech.edu/lane/1232> ;
    libns:library_id "11011"@en ;
    libns:library_type "None"@en ;
    a libns:Library ;
    <http://www.w3.org/1999/xhtml/vocab#stylesheet> <http://jumpgate.caltech.edu/static/css/app.css>, <http://jumpgate.caltech.edu/static/css/data-browse-index.css> .

_:bnode110110
    a libns:MappedCount ;
    libns:mapped_to "newcontam_UK.fa"@en ;
    libns:reads 42473 .

<http://jumpgate.caltech.edu/lane/1903>
    a libns:IlluminaLane ;
    libns:flowcell <http://jumpgate.caltech.edu/flowcell/62WCKAAXX/> ;
    libns:has_mappings _:bnode120970 ;
    libns:total_unique_locations 39172114 .

<http://jumpgate.caltech.edu/library/12097/>
    libns:has_lane <http://jumpgate.caltech.edu/lane/1903> ;
    libns:library_id "12097"@en ;
    libns:library_type "Paired End (non-multiplexed)"@en ;
    a libns:Library .

_:bnode120970
    a libns:MappedCount ;
    libns:mapped_to "newcontam_UK.fa"@en ;
    libns:reads 64 .
''', 'http://jumpgate.caltech.edu/library')
        errmsgs = list(self.inference.run_validation())
        self.assertEqual(len(errmsgs), 0)
        urn = RDF.Node(RDF.Uri('http://jumpgate.caltech.edu/library/11011/'))
        encode_find.delete_library(self.model, urn)
        q = RDF.Statement(None, encode_find.libraryOntology['reads'], None)
        stmts = list(self.model.find_statements(q))
        self.failUnlessEqual(len(stmts), 1)
        self.failUnlessEqual(fromTypedNode(stmts[0].object),
                             64)

        q = RDF.Statement(None, encode_find.libraryOntology['library_id'], None)
        stmts = list(self.model.find_statements(q))
        self.failUnlessEqual(len(stmts), 1)
        self.failUnlessEqual(fromTypedNode(stmts[0].object),
                             '12097')

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestEncodeFind))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main()
