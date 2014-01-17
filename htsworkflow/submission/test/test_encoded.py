import json
import os
from pprint import pprint
from unittest2 import TestCase, TestSuite, defaultTestLoader, skip

from htsworkflow.submission.encoded import (ENCODED,
     ENCODED_CONTEXT,
     ENCODED_NAMESPACES
)

class TestEncoded(TestCase):
    def test_prepare_url(self):
        encode = ENCODED('test.encodedcc.edu')

        tests = [
            ('/experiments', 'http://test.encodedcc.edu/experiments'),
            ('/experiments/ENCLB045ZZZ',
             'http://test.encodedcc.edu/experiments/ENCLB045ZZZ'),
            ('http://submit.encodedcc.edu/experiments/ENCLB045ZZZ',
             'http://submit.encodedcc.edu/experiments/ENCLB045ZZZ'),
        ]
        for url, result in tests:
            self.assertEqual(encode.prepare_url(url), result)

    def test_validate(self):
        """Test validation
        """
        schema_file = os.path.join(os.path.dirname(__file__), 'library.json')
        schema = json.loads(open(schema_file, 'r').read())

        obj = {u'@id': u'/libraries/ENCLB045ZZZ/',
               u'@type': [u'library', u'item'],
               u'accession': u'ENCLB045ZZZ',
               u'aliases': [],
               u'alternate_accessions': [],
               u'award': u'/awards/U54HG006998/',
               u'biosample': u'/biosamples/ENCBS089RNA/',
               u'date_created': u'2014-01-14T19:44:51.061770+00:00',
               u'depleted_in_term_id': [],
               u'depleted_in_term_name': [],
               u'documents': [],
               u'extraction_method': u'Ambion mirVana',
               u'fragmentation_method': u'Illumina/Nextera tagmentation',
               u'lab': u'/labs/barbara-wold/',
               u'library_size_selection_method': u'SPRI beads',
               u'lysis_method': u'Ambion mirVana',
               u'nucleic_acid_term_id': u'SO:0000871',
               u'nucleic_acid_term_name': u'polyadenylated mRNA',
               u'paired_ended': False,
               u'schema_version': u'2',
               u'size_range': u'>200',
               u'status': u'CURRENT',
               u'strand_specificity': False,
               u'submitted_by': u'/users/0e3dde9b-aaf9-42dd-87f7-975a85072ed2/',
               u'treatments': [],
               u'uuid': u'42c46028-708f-4347-a3df-2c82dfb021c4'}
        encode = ENCODED('submit.encodedcc.org')
        encode.schemas[u'library'] = schema
        encode.validate(obj)
        self.assertTrue('@id' in obj)

    def test_create_context(self):
        linked_id = {'@type': '@id'}
        library = { '@id': '/libraries/1234', '@type': ['library', 'item'] }

        encode = ENCODED('test.encodedcc.org')
        url = encode.prepare_url(library['@id'])
        context = encode.create_jsonld_context(library, url)
        self.assertEqual(context['@vocab'], 'http://test.encodedcc.org/profiles/library.json#')
        self.assertEqual(context['award'], linked_id )
        self._verify_context(context, 'library')
        # namespaces not added yet.
        self.assertRaises(AssertionError, self._verify_namespaces, context)
        encode.add_jsonld_namespaces(context)
        self._verify_namespaces(context)

    def test_add_context(self):
        """Checking to make sure nested @base and @vocab urls are set correctly
        """
        obj = {
            "nucleic_acid_term_name": "RNA",
            "accession": "ENCLB044ZZZ",
            "@id": "/libraries/ENCLB044ZZZ/",
            "schema_version": "1",
            "@type": [
                "library",
                "item"
            ],
            "lysis_method": "Ambion mirVana",
            "nucleic_acid_term_id": "SO:0000356",
            "biosample": {
                "biosample_term_name": "GM12878",
                "description": "B-lymphocyte, lymphoblastoid, International HapMap Project - CEPH/Utah - European Caucasion, Epstein-Barr Virus",
                "accession": "ENCBS090RNA",
                "date_created": "2013-10-29T21:15:29.144260+00:00",
                "@id": "/biosamples/ENCBS090RNA/",
                "aliases": [
                "brenton-graveley:GM12878-2",
                "thomas-gingeras:191WC"
                ],
                "organism": "/organisms/human/",
                "@type": [
                "biosample",
                "item"
                ]
            },
        }

        encode = ENCODED('test.encodedcc.org')
        bio_base = encode.prepare_url(obj['biosample']['@id'])

        url = encode.prepare_url('/libraries/ENCLB044ZZZ/?format=json&embed=False')
        schema_url = encode.get_schema_url(obj)
        encode.add_jsonld_context(obj, url)

        self.assertEqual(obj['biosample']['@context']['@base'], bio_base)
        self.assertEqual(obj['@context']['@vocab'], schema_url)
        self._verify_context(obj['@context'], 'library')
        self._verify_namespaces(obj['@context'])
        self._verify_context(obj['biosample']['@context'], 'biosample')
        self.assertEqual(obj['@context']['rdf'], 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.assertEqual(obj['@context']['OBO'], 'http://purl.obolibrary.org/obo/')


    def _verify_context(self, context, obj_type):
        for context_key in [None, obj_type]:
            for k in ENCODED_CONTEXT[context_key]:
                self.assertIn(k, context)
                self.assertEqual(ENCODED_CONTEXT[context_key][k], context[k])

    def _verify_namespaces(self, context):
        for k in ENCODED_NAMESPACES:
            self.assertIn(k, context)
            self.assertEqual(ENCODED_NAMESPACES[k], context[k])

def suite():
    suite = TestSuite()
    suite.addTests(
        defaultTestLoader.loadTestsFromTestCase(TestEncoded))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest='suite')
