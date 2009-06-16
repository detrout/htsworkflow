import datetime
import unittest
from htsworkflow.frontend.samples.models import \
        Affiliation, \
        ExperimentType, \
        Species, \
        Library

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
        library_id = 10001,
        library_name = 'C2C12 named poorly',
        library_species = obj.species_human,
        experiment_type = obj.experiment_rna_seq,
        creation_date = datetime.datetime.now(),
        made_for = 'scientist unit 2007',
        made_by = 'microfludics system 7321',
        stopping_point = '2A',
        undiluted_concentration = '5.01',
    )
    obj.library_10001.save()
    obj.library_10002 = Library(
        library_id = 10002,
        library_name = 'Worm named poorly',
        library_species = obj.species_human,
        experiment_type = obj.experiment_rna_seq,
        creation_date = datetime.datetime.now(),
        made_for = 'scientist unit 2007',
        made_by = 'microfludics system 7321',
        stopping_point = '2A',
        undiluted_concentration = '5.01',
    )
    obj.library_10002.save()
 
class LibraryTestCase(unittest.TestCase):
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

