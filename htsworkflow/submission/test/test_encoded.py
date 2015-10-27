from __future__ import absolute_import, print_function

import json
import os
from pprint import pprint
from unittest import TestCase, TestSuite, defaultTestLoader, skip

from htsworkflow.submission.encoded import (ENCODED,
     ENCODED_CONTEXT,
     ENCODED_NAMESPACES
)

class TestEncoded(TestCase):
    def test_prepare_url(self):
        encode = ENCODED('www.encodeproject.org')

        tests = [
            ('/experiments', 'https://www.encodeproject.org/experiments'),
            ('/experiments/ENCLB045ZZZ',
             'https://www.encodeproject.org/experiments/ENCLB045ZZZ'),
            ('https://www.encodeproject.org/experiments/ENCLB045ZZZ',
             'https://www.encodeproject.org/experiments/ENCLB045ZZZ'),
        ]
        for url, result in tests:
            self.assertEqual(encode.prepare_url(url), result)

    def test_validate(self):
        """Test validation
        """
        schema_file = os.path.join(os.path.dirname(__file__), 'library.json')
        schema = json.loads(open(schema_file, 'r').read())

        obj = {u'@id': u'/libraries/ENCLB045ZZZ/',
               u'@type': [u'Library', u'Item'],
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
               u'fragmentation_method': u'chemical (Nextera tagmentation)',
               u'lab': u'/labs/barbara-wold/',
               u'library_size_selection_method': u'SPRI beads',
               u'lysis_method': u'Ambion mirVana',
               u'nucleic_acid_term_id': u'SO:0000871',
               u'nucleic_acid_term_name': u'polyadenylated mRNA',
               u'schema_version': u'2',
               u'size_range': u'>200',
               u'status': u'released',
               u'strand_specificity': False,
               u'submitted_by': u'/users/0e3dde9b-aaf9-42dd-87f7-975a85072ed2/',
               u'treatments': [],
               u'uuid': u'42c46028-708f-4347-a3df-2c82dfb021c4'}
        encode = ENCODED('www.encodeproject.org')
        encode.schemas[u'library'] = schema
        encode.validate(obj)
        self.assertTrue('@id' in obj)

    def test_create_context(self):
        linked_id = {'@type': '@id'}
        library = { '@id': '/libraries/1234', '@type': ['Library', 'Item'] }

        encode = ENCODED('www.encodeproject.org')
        url = encode.prepare_url(library['@id'])
        context = encode.create_jsonld_context(library, url)
        self.assertEqual(context['@vocab'], 'https://www.encodeproject.org/profiles/Library.json#')
        self.assertEqual(context['award'], linked_id )
        self._verify_context(context, 'Library')
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
                "Library",
                "Item"
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
                "Biosample",
                "Item"
                ]
            },
        }

        encode = ENCODED('www.encodeproject.org')
        bio_base = encode.prepare_url(obj['biosample']['@id'])

        url = encode.prepare_url('/libraries/ENCLB044ZZZ/?format=json&embed=False')
        obj_type = encode.get_object_type(obj)
        schema_url = encode.get_schema_url(obj_type)
        encode.add_jsonld_context(obj, url)

        self.assertEqual(obj['biosample']['@context']['@base'], bio_base)
        self.assertEqual(obj['@context']['@vocab'], schema_url)
        self._verify_context(obj['@context'], 'Library')
        self._verify_namespaces(obj['@context'])
        self._verify_context(obj['biosample']['@context'], 'Biosample')
        self.assertEqual(obj['@context']['rdf'], 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.assertEqual(obj['@context']['OBO'], 'http://purl.obolibrary.org/obo/')


    def test_convert_search_to_jsonld(self):
        example = {'count': {'biosamples': 2},
                   'portal_title': 'ENCODE',
                   'title': 'Search',
                   'notification': 'Success',
                   'filters': [],
                   '@id': '/search/?searchTerm=wold',
                   '@type': ['search'],
                   'facets': [],
                    '@graph': [{
                    u'@id': u'/biosamples/ENCBS125ENC/',
                    u'@type': [u'Biosample', u'Item'],
                    u'accession': u'ENCBS125ENC',
                    u'award.rfa': u'ENCODE2-Mouse',
                    u'biosample_term_name': u'myocyte',
                    u'biosample_type': u'in vitro differentiated cells',
                    u'characterizations.length': [],
                    u'constructs.length': [],
                    u'lab.title': u'Barbara Wold, Caltech',
                    u'life_stage': u'unknown',
                    u'organism.name': u'mouse',
                    u'source.title': u'Barbara Wold',
                    u'status': u'CURRENT',
                    u'treatments.length': []},
                    {u'@id': u'/biosamples/ENCBS126ENC/',
                    u'@type': [u'Biosample', u'Item'],
                    u'accession': u'ENCBS126ENC',
                    u'award.rfa': u'ENCODE2-Mouse',
                    u'biosample_term_name': u'myocyte',
                    u'biosample_type': u'in vitro differentiated cells',
                    u'characterizations.length': [],
                    u'constructs.length': [],
                    u'lab.title': u'Barbara Wold, Caltech',
                    u'life_stage': u'unknown',
                    u'organism.name': u'mouse',
                    u'source.title': u'Barbara Wold',
                    u'status': u'CURRENT',
                    u'treatments.length': []},
                    ]}

        encode = ENCODED('www.encodeproject.org')
        result = encode.convert_search_to_jsonld(example)
        for obj in result['@graph']:
            self.assertNotIn('award.rfa', obj)

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
    from unittest import main
    main(defaultTest='suite')
