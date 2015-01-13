from __future__ import absolute_import, print_function

import datetime

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText, FuzzyInteger
from experiments.experiments_factory import FlowCellFactory
from samples.samples_factory import LibraryFactory
from . import models
#from bcmagic.factory import PrinterFactory

class VendorFactory(DjangoModelFactory):
    class Meta:
        model = models.Vendor

    name = FuzzyText(prefix='vendor name ')
    url = FuzzyText(prefix='https://vendor.example.org/')


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = models.Location

    name = FuzzyText(prefix='location name ')
    location_description = FuzzyText(prefix='location ')
    notes = FuzzyText(prefix='note ')


class ItemInfoFactory(DjangoModelFactory):
    class Meta:
        model = models.ItemInfo

    model_id = FuzzyText(prefix='model ')
    part_number = FuzzyText(prefix='part ')
    lot_number = FuzzyText(prefix='lot ')
    url = factory.LazyAttribute(lambda o: 'http://example.com/{}'.format(o.model_id))
    qty_purchased = FuzzyInteger(1, 50)

    vendor = factory.SubFactory(VendorFactory)
    purchase_date = datetime.datetime.now()
    warranty_months = 30


class ItemTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.ItemType

    name = FuzzyText(prefix='item type name ')
    description = FuzzyText(prefix='item type description ')


class ItemStatusFactory(DjangoModelFactory):
    class Meta:
        model = models.ItemStatus

    name = FuzzyText(prefix='item status ')
    notes = FuzzyText(prefix='item status description ')


class ItemFactory(DjangoModelFactory):
    class Meta:
        model = models.Item

    barcode_id = FuzzyText(length=12, chars='0123456789')
    force_use_uuid = True
    item_type = factory.SubFactory(ItemTypeFactory)
    item_info = factory.SubFactory(ItemInfoFactory)
    location = factory.SubFactory(LocationFactory)
    status = factory.SubFactory(ItemStatusFactory)
    creation_date = datetime.datetime.now()
    modified_date = creation_date
    notes = FuzzyText(prefix='Item notes ')


class PrinterTemplateFactory(DjangoModelFactory):
    class Meta:
        model = models.PrinterTemplate

    item_type = factory.SubFactory(ItemTypeFactory)
    #printer = factory.SubFactory(PrinterFactory)
    default = True
    template = 'template'


class LongTermStorageFactory(DjangoModelFactory):
    class Meta:
        model = models.LongTermStorage

    flowcell = factory.SubFactory(FlowCellFactory)
    # libraries = many to many Library
    # storage_devices = many to many Item
    creation_date = datetime.datetime.now()
    modified_date = creation_date

    @factory.post_generation
    def libraries(self, create, extracted, **kwargs):
        if extracted:
            for e in extracted:
                self.libraries.add(e)

    @factory.post_generation
    def storage_devices(self, create, extracted, **kwargs):
        if extracted:
            for e in extracted:
                self.storage_devices.add(e)

class ReagentBaseFactory(DjangoModelFactory):
    class Meta:
        model = models.ReagentBase

    #reagent = many to many Item
    creation_date = datetime.datetime.now()
    modification_date = creation_date


class ReagentFlowcellFactory(DjangoModelFactory):
    class Meta:
        model = models.ReagentFlowcell

    flowcell = factory.SubFactory(FlowCellFactory)

class ReagentLibraryFactory(DjangoModelFactory):
    class Meta:
        model = models.ReagentLibrary

    library = factory.SubFactory(LibraryFactory)
