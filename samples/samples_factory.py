import datetime

import factory
from factory.django import DjangoModelFactory
from . import models

class AffiliationFactory(DjangoModelFactory):
    class Meta:
        model = models.Affiliation

    name = 'affiliation'
    contact = 'contact name'
    email = factory.LazyAttribute(lambda obj: '%s@example.com' % obj.name)

    @factory.post_generation
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

    name = 'experiment type name'

class HTSUserFactory(DjangoModelFactory):
    class Meta:
        model = models.HTSUser

    username = 'username'
    email = factory.LazyAttribute(lambda obj: '%s@example.org' % obj.username)
    
#class Tag

class SpeciesFactory(DjangoModelFactory):
    class Meta:
        model = models.Species

    scientific_name = 'test sapiens'
    common_name = 'test human'

        
class LibraryFactory(DjangoModelFactory):
    class Meta:
        model = models.Library

    id = '10001'
    library_name = 'C1C1 test'
    library_species = factory.SubFactory(SpeciesFactory)
    experiment_type = factory.SubFactory(ExperimentTypeFactory)
    creation_date = datetime.datetime.now()
    gel_cut_size = 400
    made_for = 'scientist unit 2007'
    made_by = 'microfluidics bot 7321'
    stopping_point = '2A'
    undiluted_concentration = '5.01'
    hidden = False
