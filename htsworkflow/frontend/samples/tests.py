import datetime
import unittest

try:
    import json
except ImportError, e:
    import simplejson as json
    
from django.test import TestCase

from htsworkflow.frontend.samples.models import \
        Affiliation, \
        ExperimentType, \
        Species, \
        Library

from htsworkflow.frontend.samples.views import \
     library_dict, \
     library_json

from htsworkflow.frontend.auth import apidata
from htsworkflow.util.conversion import unicode_or_none


class LibraryTestCase(TestCase):
    fixtures = ['test_samples.json']

    def setUp(self):
        create_db(self)
               
    def testOrganism(self):
        self.assertEquals(self.library_10001.organism(), 'human')

    def testAffiliations(self):
        self.library_10001.affiliations.add(self.affiliation_alice)
        self.library_10002.affiliations.add(
                self.affiliation_alice, 
                self.affiliation_bob
        )
        self.failUnless(len(self.library_10001.affiliations.all()), 1)
        self.failUnless(self.library_10001.affiliation(), 'Alice')

        self.failUnless(len(self.library_10002.affiliations.all()), 2)
        self.failUnless(self.library_10001.affiliation(), 'Alice, Bob')


class SampleWebTestCase(TestCase):
    """
    Test returning data from our database in rest like ways.
    (like returning json objects)
    """
    fixtures = ['test_samples.json']

    def test_library_info(self):

        for lib in Library.objects.all():
            lib_dict = library_dict(lib.id)
            url = '/samples/library/%s/json' % (lib.id,)
            lib_response = self.client.get(url, apidata)
            self.failUnlessEqual(lib_response.status_code, 200)
            lib_json = json.loads(lib_response.content)

            for d in [lib_dict, lib_json]:
                # amplified_from_sample is a link to the library table,
                # I want to use the "id" for the data lookups not
                # the embedded primary key.
                # It gets slightly confusing on how to implement sending the right id
                # since amplified_from_sample can be null
                #self.failUnlessEqual(d['amplified_from_sample'], lib.amplified_from_sample)
                self.failUnlessEqual(d['antibody_id'], lib.antibody_id)
                self.failUnlessEqual(d['cell_line_id'], lib.cell_line_id)
                self.failUnlessEqual(d['cell_line'], unicode_or_none(lib.cell_line))
                self.failUnlessEqual(d['experiment_type'], lib.experiment_type.name)
                self.failUnlessEqual(d['experiment_type_id'], lib.experiment_type_id)
                self.failUnlessEqual(d['gel_cut_size'], lib.gel_cut_size)
                self.failUnlessEqual(d['hidden'], lib.hidden)
                self.failUnlessEqual(d['id'], lib.id)
                self.failUnlessEqual(d['insert_size'], lib.insert_size)
                self.failUnlessEqual(d['library_name'], lib.library_name)
                self.failUnlessEqual(d['library_species'], lib.library_species.scientific_name)
                self.failUnlessEqual(d['library_species_id'], lib.library_species_id)
                self.failUnlessEqual(d['library_type_id'], lib.library_type_id)
                if lib.library_type_id is not None:
                    self.failUnlessEqual(d['library_type'], lib.library_type.name)
                else:
                    self.failUnlessEqual(d['library_type'], None)
                    self.failUnlessEqual(d['made_for'], lib.made_for)
                    self.failUnlessEqual(d['made_by'], lib.made_by)
                    self.failUnlessEqual(d['notes'], lib.notes)
                    self.failUnlessEqual(d['replicate'], lib.replicate)
                    self.failUnlessEqual(d['stopping_point'], lib.stopping_point)
                    self.failUnlessEqual(d['successful_pM'], lib.successful_pM)
                    self.failUnlessEqual(d['undiluted_concentration'],
                                         unicode(lib.undiluted_concentration))
                # some specific tests
                if lib.id == '10981':
                    # test a case where there is no known status
                    lane_set = {u'status': u'Unknown', u'paired_end': True, u'read_length': 75, u'lane_number': 1, u'flowcell': u'303TUAAXX', u'status_code': None}
                    self.failUnlessEqual(len(d['lane_set']), 1)
                    self.failUnlessEqual(d['lane_set'][0], lane_set)
                elif lib.id == '11016':
                    # test a case where there is a status
                    lane_set = {u'status': 'Good', u'paired_end': True, u'read_length': 75, u'lane_number': 5, u'flowcell': u'303TUAAXX', u'status_code': 2}
                    self.failUnlessEqual(len(d['lane_set']), 1)
                    self.failUnlessEqual(d['lane_set'][0], lane_set)

    def test_invalid_library(self):
        """
        Make sure we get a 404 if we request an invalid library id
        """
        response = self.client.get('/samples/library/nottheone/json', apidata)
        self.failUnlessEqual(response.status_code, 404)

            
    def test_library_no_key(self):
        """
        Make sure we get a 302 if we're not logged in
        """
        response = self.client.get('/samples/library/10981/json')
        self.failUnlessEqual(response.status_code, 403)
        response = self.client.get('/samples/library/10981/json', apidata)
        self.failUnlessEqual(response.status_code, 200)

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
except ImportError,e:
    HAVE_RDF = False

    
class TestRDFaLibrary(TestCase):
    fixtures = ['test_samples.json']

    def test_parse_rdfa(self):
        model = get_rdf_memory_model()
        parser = RDF.Parser(name='rdfa')
        url = '/library/10981/'
        lib_response = self.client.get(url)
        self.failIfEqual(len(lib_response.content), 0)
        
        parser.parse_string_into_model(model,
                                       lib_response.content,
                                       'http://localhost'+url)
        # http://jumpgate.caltech.edu/wiki/LibraryOntology#affiliation>
        self.check_literal_object(model, ['Bob'], p=libNS['affiliation'])
        self.check_literal_object(model, ['Multiplexed'], p=libNS['experiment_type'])
        self.check_literal_object(model, ['400'], p=libNS['gel_cut'])
        self.check_literal_object(model, ['Igor'], p=libNS['made_by'])
        self.check_literal_object(model, ['Paired End Multiplexed Sp-BAC'], p=libNS['name'])
        self.check_literal_object(model, ['Drosophila melanogaster'], p=libNS['species'])

        self.check_uri_object(model,
                              [u'http://localhost/lane/1193'],
                              p=libNS['has_lane'])

        self.check_literal_object(model,
                                  [u"303TUAAXX"],
                                  s=RDF.Uri('http://localhost/flowcell/303TUAAXX/'))
                                  
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

