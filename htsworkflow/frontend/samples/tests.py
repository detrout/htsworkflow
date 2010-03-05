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

# The django test runner flushes the database between test suites not cases,
# so to be more compatible with running via nose we flush the database tables
# of interest before creating our sample data.
def create_db(obj):
    Species.objects.all().delete()
    obj.species_human = Species(
        scientific_name = 'Homo Sapeins',
        common_name = 'human',
    )
    obj.species_human.save()
    obj.species_worm = Species(
        scientific_name = 'C. Elegans',
        common_name = 'worm',
    )
    obj.species_worm.save()
    obj.species_phix = Species(
        scientific_name = 'PhiX',
        common_name = 'PhiX'
    )
    obj.species_phix.save()

    ExperimentType.objects.all().delete()
    obj.experiment_de_novo = ExperimentType(
        name = 'De Novo',
    )
    obj.experiment_de_novo.save()
    obj.experiment_chip_seq = ExperimentType(
        name = 'ChIP-Seq'
    )
    obj.experiment_chip_seq.save()
    obj.experiment_rna_seq = ExperimentType(
        name = 'RNA-Seq'
    )
    obj.experiment_rna_seq.save()

    Affiliation.objects.all().delete()
    obj.affiliation_alice = Affiliation(
        name = 'Alice',
        contact = 'Lab Boss',
        email = 'alice@some.where.else.'
    )
    obj.affiliation_alice.save()
    obj.affiliation_bob = Affiliation(
        name = 'Bob',
        contact = 'Other Lab Boss',
        email = 'bob@some.where.else',
    )
    obj.affiliation_bob.save()

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
 
class LibraryTestCase(TestCase):
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
                self.failUnlessEqual(d['avg_lib_size'], lib.avg_lib_size)
                self.failUnlessEqual(d['cell_line_id'], lib.cell_line_id)
                self.failUnlessEqual(d['cell_line'], unicode_or_none(lib.cell_line))
                self.failUnlessEqual(d['experiment_type'], lib.experiment_type.name)
                self.failUnlessEqual(d['experiment_type_id'], lib.experiment_type_id)
                self.failUnlessEqual(d['hidden'], lib.hidden)
                self.failUnlessEqual(d['id'], lib.id)
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
