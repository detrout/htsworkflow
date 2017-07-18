from __future__ import unicode_literals

from django.utils import timezone

from factory import LazyAttribute, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText
from . import models


class AffiliationFactory(DjangoModelFactory):
    class Meta:
        model = models.Affiliation

    name = FuzzyText(prefix='affiliation ')
    contact = 'contact name'
    email = LazyAttribute(lambda obj: '%s@example.com' % obj.name)

    @post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.users.add(user)

class AntibodyFactory(DjangoModelFactory):
    class Meta:
        model = models.Antibody
        django_get_or_create = ('antigene',)

    antigene = 'antigene'
    nickname = 'short name'
    catalog = 'catalog #'
    antibodies = 'antibody'
    source = 'source'
    biology = 'some biological description'
    notes = 'some notes'


class CelllineFactory(DjangoModelFactory):
    class Meta:
        model = models.Cellline

    cellline_name = 'Test'
    nickname = 'Test'
    notes = 'Notes'


class ConditionFactory(DjangoModelFactory):
    class Meta:
        model = models.Condition

    condition_name = 'condition name'
    nicname = 'nickname'
    notes = 'notes'

class ExperimentTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.ExperimentType
        django_get_or_create = ('name',)

    name = 'experiment type name'

class HTSUserFactory(DjangoModelFactory):
    class Meta:
        model = models.HTSUser
        django_get_or_create = ('username',)

    username = 'username'
    email = LazyAttribute(lambda obj: '%s@example.org' % obj.username)
    is_staff = False
    is_superuser = False

#class Tag

class SpeciesFactory(DjangoModelFactory):
    class Meta:
        model = models.Species

    scientific_name = FuzzyText(prefix='scientific name ')
    common_name = FuzzyText(prefix='common name ')

class LibraryTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.LibraryType

    is_paired_end = FuzzyChoice([True, False])
    can_multiplex = FuzzyChoice([True, False])
    name = FuzzyText(prefix='library type ')

class MultiplexIndexFactory(DjangoModelFactory):
    class Meta:
        model = models.MultiplexIndex

    adapter_type = SubFactory(LibraryTypeFactory)
    multiplex_id = LazyAttribute(lambda o: 'N{}'.format(o.sequence))
    sequence = FuzzyText(length=5, chars='AGCT')

class LibraryFactory(DjangoModelFactory):
    class Meta:
        model = models.Library

    id = Sequence(lambda n: str(10000 + n))
    library_name = LazyAttribute(lambda o: 'Library %s' % (o.id))
    library_species = SubFactory(SpeciesFactory)
    experiment_type = SubFactory(ExperimentTypeFactory)
    creation_date = timezone.now()
    gel_cut_size = 400
    made_for = 'scientist unit 2007'
    made_by = 'microfluidics bot 7321'
    stopping_point = '2A'
    undiluted_concentration = '5.01'
    hidden = False
    library_type = SubFactory(LibraryTypeFactory)


class AccessionAgencyFactory(DjangoModelFactory):
    class Meta:
        model = models.AccessionAgency

    name = FuzzyText(prefix="agency ")
    homepage = FuzzyText(prefix="http://", suffix=".example.com")
    library_template = LazyAttribute(lambda o: "%s/library/{}" % (o.homepage,))


class LibraryAccessionFactory(DjangoModelFactory):
    class Meta:
        model = models.LibraryAccession

    accession = FuzzyText(prefix="ACC")
    agency = SubFactory(AccessionAgencyFactory)
    created = timezone.now()
