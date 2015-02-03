from __future__ import absolute_import, print_function, unicode_literals

import logging

from django.db import models
from django.db.models.signals import pre_save, post_init

from samples.models import Library
from experiments.models import FlowCell
from bcmagic.models import Printer

LOGGER = logging.getLogger(__name__)

try:
    import uuid
except ImportError as e:
    # Some systems are using python 2.4, which doesn't have uuid
    # this is a stub
    LOGGER.warning('Real uuid is not available, initializing fake uuid module')

    class uuid:
        def uuid1(self):
            self.hex = None
            return self


def _assign_uuid(sender, instance, **kwargs):
    """
    Assigns a UUID to model on save
    """
    if instance.uuid is None or len(instance.uuid) != 32:
        instance.uuid = uuid.uuid1().hex


def _switch_default(sender, instance, **kwargs):
    """
    When new instance has default == True, uncheck all other defaults
    """
    if instance.default:
        other_defaults = PrinterTemplate.objects.filter(default=True)

        for other in other_defaults:
            other.default = False
            other.save()


class Vendor(models.Model):
    name = models.CharField(max_length=256)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return "%s" % (self.name)


class Location(models.Model):

    name = models.CharField(max_length=256, unique=True)
    location_description = models.TextField()

    uuid = models.CharField(max_length=32,
                            blank=True,
                            help_text="Leave blank for automatic UUID generation",
                            editable=False)

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        if len(self.location_description) > 16:
            return "%s: %s" % (self.name, self.location_description[0:16]+"...")
        else:
            return "%s: %s" % (self.name, self.location_description)

post_init.connect(_assign_uuid, sender=Location)


class ItemInfo(models.Model):
    model_id = models.CharField(max_length=256, blank=True, null=True)
    part_number = models.CharField(max_length=256, blank=True, null=True)
    lot_number = models.CharField(max_length=256, blank=True, null=True)

    url = models.URLField(blank=True, null=True)

    qty_purchased = models.IntegerField(default=1)

    vendor = models.ForeignKey(Vendor)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_months = models.IntegerField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        name = u''
        if self.model_id:
            name += "model:%s " % (self.model_id)
        if self.part_number:
            name += "part:%s " % (self.part_number)
        if self.lot_number:
            name += "lot:%s " % (self.lot_number)

        return "%s: %s" % (name, self.purchase_date)

    class Meta:
        verbose_name_plural = "Item Info"


class ItemType(models.Model):

    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s" % (self.name)


class ItemStatus(models.Model):
    name = models.CharField(max_length=64, unique=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Item Status"


class Item(models.Model):
    item_type = models.ForeignKey(ItemType)

    #Automatically assigned uuid; used for barcode if one is not provided in
    # barcode_id
    uuid = models.CharField(max_length=32,
                            blank=True,
                            help_text="Leave blank for automatic UUID generation",
                            unique=True,
                            editable=False)

    # field for existing barcodes; used instead of uuid if provided
    barcode_id = models.CharField(max_length=256, blank=True, null=True)
    force_use_uuid = models.BooleanField(default=False)

    item_info = models.ForeignKey(ItemInfo)

    location = models.ForeignKey(Location)

    status = models.ForeignKey(ItemStatus, blank=True, null=True)

    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.barcode_id is None or len(self.barcode_id) == 0:
            return "invu|%s" % (self.uuid)
        else:
            return "invb|%s" % (self.barcode_id)

    def get_absolute_url(self):
        return '/inventory/%s/' % (self.uuid)

post_init.connect(_assign_uuid, sender=Item)


class PrinterTemplate(models.Model):
    """
    Maps templates to printer to use
    """
    item_type = models.ForeignKey(ItemType)
    printer = models.ForeignKey(Printer)

    default = models.BooleanField(default=False)

    template = models.TextField()

    def __str__(self):
        if self.default:
            return u'%s %s' % (self.item_type.name, self.printer.name)
        else:
            return u'%s %s (default)' % (self.item_type.name, self.printer.name)

pre_save.connect(_switch_default, sender=PrinterTemplate)


class LongTermStorage(models.Model):
    flowcell = models.ForeignKey(FlowCell)
    libraries = models.ManyToManyField(Library)

    storage_devices = models.ManyToManyField(Item)

    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s: %s" % (str(self.flowcell), ', '.join([str(s) for s in self.storage_devices.iterator()]))

    class Meta:
        verbose_name_plural = "Long Term Storage"


class ReagentBase(models.Model):
    reagent = models.ManyToManyField(Item)

    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReagentFlowcell(ReagentBase):
    """
    Links reagents and flowcells
    """
    flowcell = models.ForeignKey(FlowCell)

    def __str__(self):
        return "%s: %s" % (str(self.flowcell), ', '.join([str(s) for s in self.reagent.iterator()]))


class ReagentLibrary(ReagentBase):
    """
    Links libraries and flowcells
    """
    library = models.ForeignKey(Library)

    def __str__(self):
        return "%s: %s" % (str(self.library), ', '.join([str(s) for s in self.reagent.iterator()]))
