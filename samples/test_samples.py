from __future__ import absolute_import, print_function

import datetime
import unittest
import json

from django.test import TestCase, RequestFactory
from django.conf import settings

from .models import Affiliation, ExperimentType, Species, Library
from .views import library_dict, library_json, library
from .samples_factory import *

from htsworkflow.auth import apidata
from htsworkflow.util.conversion import unicode_or_none
from htsworkflow.util.ethelp import validate_xhtml

class LibraryTestCase(TestCase):
    def testOrganism(self):
        human = SpeciesFactory(common_name='human')
        self.assertEquals(human.common_name, 'human')
        library = LibraryFactory(library_species=human)
        self.assertEquals(library.organism(), 'human')

    def testAddingOneAffiliation(self):
        affiliation = AffiliationFactory.create(name='Alice')
        library = LibraryFactory()
        library.affiliations.add(affiliation)

        self.assertEqual(len(library.affiliations.all()), 1)
        self.assertEqual(library.affiliation(), 'Alice (contact name)')

    def testMultipleAffiliations(self):
        alice = AffiliationFactory.create(name='Alice')
        bob = AffiliationFactory.create(name='Bob')

        library = LibraryFactory()
        library.affiliations.add(alice, bob)

        self.assertEqual(len(library.affiliations.all()), 2)
        self.assertEqual(library.affiliation(),
                         'Alice (contact name), Bob (contact name)')


class SampleWebTestCase(TestCase):
    """
    Test returning data from our database in rest like ways.
    (like returning json objects)
    """
    def test_library_dict(self):
        library = LibraryFactory.create()
        lib_dict = library_dict(library.id)
        url = '/samples/library/%s/json' % (library.id,)
        lib_response = self.client.get(url, apidata)
        lib_json = json.loads(lib_response.content)['result']

        for d in [lib_dict, lib_json]:
            # amplified_from_sample is a link to the library table,
            # I want to use the "id" for the data lookups not
            # the embedded primary key.
            # It gets slightly confusing on how to implement sending the right id
            # since amplified_from_sample can be null
            #self.failUnlessEqual(d['amplified_from_sample'], lib.amplified_from_sample)
            self.failUnlessEqual(d['antibody_id'], library.antibody_id)
            self.failUnlessEqual(d['cell_line_id'], library.cell_line_id)
            self.failUnlessEqual(d['cell_line'], unicode_or_none(library.cell_line))
            self.failUnlessEqual(d['experiment_type'], library.experiment_type.name)
            self.failUnlessEqual(d['experiment_type_id'], library.experiment_type_id)
            self.failUnlessEqual(d['gel_cut_size'], library.gel_cut_size)
            self.failUnlessEqual(d['hidden'], library.hidden)
            self.failUnlessEqual(d['id'], library.id)
            self.failUnlessEqual(d['insert_size'], library.insert_size)
            self.failUnlessEqual(d['library_name'], library.library_name)
            self.failUnlessEqual(d['library_species'], library.library_species.scientific_name)
            self.failUnlessEqual(d['library_species_id'], library.library_species_id)
            self.failUnlessEqual(d['library_type_id'], library.library_type_id)
            self.assertTrue(d['library_type'].startswith('library type'))
            self.failUnlessEqual(d['made_for'], library.made_for)
            self.failUnlessEqual(d['made_by'], library.made_by)
            self.failUnlessEqual(d['notes'], library.notes)
            self.failUnlessEqual(d['replicate'], library.replicate)
            self.failUnlessEqual(d['stopping_point'], library.stopping_point)
            self.failUnlessEqual(d['successful_pM'], library.successful_pM)
            self.failUnlessEqual(d['undiluted_concentration'],
                                 unicode(library.undiluted_concentration))


        def junk(self):
                # some specific tests
                if library.id == '10981':
                    # test a case where there is no known status
                    lane_set = {u'status': u'Unknown',
                                u'paired_end': True,
                                u'read_length': 75,
                                u'lane_number': 1,
                                u'lane_id': 1193,
                                u'flowcell': u'303TUAAXX',
                                u'status_code': None}
                    self.failUnlessEqual(len(d['lane_set']), 1)
                    self.failUnlessEqual(d['lane_set'][0], lane_set)
                elif library.id == '11016':
                    # test a case where there is a status
                    lane_set = {u'status': 'Good',
                                u'paired_end': True,
                                u'read_length': 75,
                                u'lane_number': 5,
                                u'lane_id': 1197,
                                u'flowcell': u'303TUAAXX',
                                u'status_code': 2}
                    self.failUnlessEqual(len(d['lane_set']), 1)
                    self.failUnlessEqual(d['lane_set'][0], lane_set)


    def test_invalid_library_json(self):
        """
        Make sure we get a 404 if we request an invalid library id
        """
        response = self.client.get('/samples/library/nottheone/json', apidata)
        self.failUnlessEqual(response.status_code, 404)


    def test_invalid_library(self):
        response = self.client.get('/library/nottheone/')
        self.failUnlessEqual(response.status_code, 404)


    def test_library_no_key(self):
        """
        Make sure we get a 403 if we're not logged in
        """
        library = LibraryFactory.create()

        url = '/samples/library/{}/json'.format(library.id)
        response = self.client.get(url, apidata)
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 403)

    def test_library_rdf(self):
        library = LibraryFactory.create()

        import RDF
        from htsworkflow.util.rdfhelp import get_model, \
             dump_model, \
             fromTypedNode, \
             load_string_into_model, \
             rdfNS, \
             libraryOntology
        model = get_model()

        response = self.client.get(library.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content
        load_string_into_model(model, 'rdfa', content)

        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?name ?library_id ?gel_cut ?made_by
        where {
           ?library a libns:library ;
                    libns:name ?name ;
                    libns:library_id ?library_id ;
                    libns:gel_cut ?gel_cut ;
                    libns:made_by ?made_by
        }"""
        query = RDF.SPARQLQuery(body)
        for r in query.execute(model):
            self.assertEqual(fromTypedNode(r['library_id']),
                             library.id)
            self.assertEqual(fromTypedNode(r['name']),
                             library.name)
            self.assertEqual(fromTypedNode(r['gel_cut']),
                             library.gel_cut)
            self.assertEqual(fromTypedNode(r['made_by']),
                             library.made_by)

        state = validate_xhtml(content)
        if state is not None:
            self.assertTrue(state)

        # validate a library page.
        from htsworkflow.util.rdfhelp import add_default_schemas
        from htsworkflow.util.rdfinfer import Infer
        add_default_schemas(model)
        inference = Infer(model)
        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

    def test_library_index_rdfa(self):
        from htsworkflow.util.rdfhelp import \
             add_default_schemas, get_model, load_string_into_model, \
             dump_model
        from htsworkflow.util.rdfinfer import Infer

        model = get_model()
        add_default_schemas(model)
        inference = Infer(model)

        response = self.client.get('/library/')
        self.assertEqual(response.status_code, 200)
        load_string_into_model(model, 'rdfa', response.content)

        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

        body =  """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?library_id ?name ?species ?species_name
        where {
           ?library a libns:Library .
           OPTIONAL { ?library libns:library_id ?library_id . }
           OPTIONAL { ?library libns:species ?species .
                      ?species libns:species_name ?species_name . }
           OPTIONAL { ?library libns:name ?name . }
        }"""
        bindings = set(['library', 'library_id', 'name', 'species', 'species_name'])
        query = RDF.SPARQLQuery(body)
        count = 0
        for r in query.execute(model):
            count += 1
            for name, value in r.items():
                self.assertTrue(name in bindings)
                self.assertTrue(value is not None)

        self.assertEqual(count, len(Library.objects.filter(hidden=False)))

        state = validate_xhtml(response.content)
        if state is not None: self.assertTrue(state)


# The django test runner flushes the database between test suites not cases,
# so to be more compatible with running via nose we flush the database tables
# of interest before creating our sample data.
def create_db(obj):
    obj.species_human = Species.objects.get(pk=8)
    obj.experiment_rna_seq = ExperimentType.objects.get(pk=4)
    obj.affiliation_alice = Affiliation.objects.get(pk=1)
    obj.affiliation_bob = Affiliation.objects.get(pk=2)

    Library.objects.all().delete()
    obj.library_10001 = Library(
        id = "10001",
        library_name = 'C2C12 named poorly',
        library_species = obj.species_human,
        experiment_type = obj.experiment_rna_seq,
        creation_date = datetime.datetime.now(),
        made_for = 'scientist unit 2007',
        made_by = 'microfludics system 7321',
        stopping_point = '2A',
        undiluted_concentration = '5.01',
        hidden = False,
    )
    obj.library_10001.save()
    obj.library_10002 = Library(
        id = "10002",
        library_name = 'Worm named poorly',
        library_species = obj.species_human,
        experiment_type = obj.experiment_rna_seq,
        creation_date = datetime.datetime.now(),
        made_for = 'scientist unit 2007',
        made_by = 'microfludics system 7321',
        stopping_point = '2A',
        undiluted_concentration = '5.01',
        hidden = False,
    )
    obj.library_10002.save()

try:
    import RDF
    HAVE_RDF = True

    rdfNS = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    xsdNS = RDF.NS("http://www.w3.org/2001/XMLSchema#")
    libNS = RDF.NS("http://jumpgate.caltech.edu/wiki/LibraryOntology#")

    from htsworkflow.util.rdfhelp import dump_model
except ImportError,e:
    HAVE_RDF = False


class TestRDFaLibrary(TestCase):

    def setUp(self):
        self.request = RequestFactory()

    def test_parse_rdfa(self):

        model = get_rdf_memory_model()
        parser = RDF.Parser(name='rdfa')

        bob = AffiliationFactory.create(name='Bob')

        lib_object = LibraryFactory()
        lib_object.affiliations.add(bob)
        url = '/library/{}/'.format(lib_object.id)
        ## request = self.request.get(url)
        ## lib_response = library(request)
        lib_response = self.client.get(url)
        with open('/tmp/body.html', 'w') as outstream:
            outstream.write(lib_response.content)
        self.failIfEqual(len(lib_response.content), 0)

        parser.parse_string_into_model(model,
                                       lib_response.content,
                                       'http://localhost'+url)
        # help debugging rdf errrors
        #with open('/tmp/test.ttl', 'w') as outstream:
        #    dump_model(model, outstream)
        # http://jumpgate.caltech.edu/wiki/LibraryOntology#affiliation>
        self.check_literal_object(model, ['Bob'], p=libNS['affiliation'])
        self.check_literal_object(model,
                                  ['experiment type name'],
                                  p=libNS['experiment_type'])
        self.check_literal_object(model, ['400'], p=libNS['gel_cut'])
        self.check_literal_object(model,
                                  ['microfluidics bot 7321'],
                                  p=libNS['made_by'])
        self.check_literal_object(model,
                                  [lib_object.library_name],
                                  p=libNS['name'])
        self.check_literal_object(model,
                                  [lib_object.library_species.scientific_name],
                                  p=libNS['species_name'])


    def check_literal_object(self, model, values, s=None, p=None, o=None):
        statements = list(model.find_statements(
            RDF.Statement(s,p,o)))
        self.failUnlessEqual(len(statements), len(values),
                        "Couln't find %s %s %s" % (s,p,o))
        for s in statements:
            self.failUnless(s.object.literal_value['string'] in values)


    def check_uri_object(self, model, values, s=None, p=None, o=None):
        statements = list(model.find_statements(
            RDF.Statement(s,p,o)))
        self.failUnlessEqual(len(statements), len(values),
                        "Couln't find %s %s %s" % (s,p,o))
        for s in statements:
            self.failUnless(unicode(s.object.uri) in values)



def get_rdf_memory_model():
    storage = RDF.MemoryStorage()
    model = RDF.Model(storage)
    return model

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(LibraryTestCase))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(SampleWebTestCase))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestRDFaLibrary))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
