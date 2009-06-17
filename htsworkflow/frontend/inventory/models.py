import logging

from django.db import models
from django.db.models.signals import pre_save

from htsworkflow.frontend.samples.models import Library
from htsworkflow.frontend.experiments.models import FlowCell


try:
    import uuid
except ImportError, e:
    # Some systems are using python 2.4, which doesn't have uuid
    # this is a stub
    logging.warning('Real uuid is not available, initializing fake uuid module')
    class uuid:
        def uuid1(self):
            self.hex = None
            return self

def _assign_uuid(sender, instance, **kwargs):
    """
    Assigns a UUID to model on save
    """
    print 'Entered _assign_uuid'
    if instance.uuid is None or len(instance.uuid) != 32:
        instance.uuid = uuid.uuid1().hex


class Vendor(models.Model):
    name = models.CharField(max_length=256)
    url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return u"%s" % (self.name)


class Location(models.Model):
    
    name = models.CharField(max_length=256, unique=True)
    location_description = models.TextField()
    
    uuid = models.CharField(max_length=32, blank=True, help_text="Leave blank for automatic UUID generation")
    
    notes = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        if len(self.location_description) > 16:
            return u"%s: %s" % (self.name, self.location_description[0:16]+u"...")
        else:
            return u"%s: %s" % (self.name, self.location_description)

pre_save.connect(_assign_uuid, sender=Location)

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
    
    def __unicode__(self):
        name = u''
        if self.model_id:
            name += u"model:%s " % (self.model_id)
        if self.part_number:
            name += u"part:%s " % (self.part_number)
        if self.lot_number:
            name += u"lot:%s " % (self.lot_number)
            
        return u"%s: %s" % (name, self.purchase_date)


class ItemType(models.Model):
    
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        return u"%s" % (self.name)

class ItemStatus(models.Model):
    name = models.CharField(max_length=64, unique=True)
    notes = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        return self.name

class Item(models.Model):
    
    item_type = models.ForeignKey(ItemType)
    
    #Automatically assigned uuid; used for barcode if one is not provided in
    # barcode_id
    uuid = models.CharField(max_length=32, blank=True, help_text="Leave blank for automatic UUID generation")
    
    # field for existing barcodes; used instead of uuid if provided
    barcode_id = models.CharField(max_length=256, blank=True, null=True)
    force_use_uuid = models.BooleanField(default=False)
    
    item_info = models.ForeignKey(ItemInfo)
    
    location = models.ForeignKey(Location)
    
    status = models.ForeignKey(ItemStatus, blank=True, null=True)
    
    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    notes = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        if self.barcode_id is None or len(self.barcode_id) == 0:
            return u"invu|%s" % (self.uuid)
        else:
            return u"invb|%s" % (self.barcode_id)
            
pre_save.connect(_assign_uuid, sender=Item)


class LongTermStorage(models.Model):
    
    flowcell = models.ForeignKey(FlowCell)
    libraries = models.ManyToManyField(Library)

    storage_devices = models.ManyToManyField(Item)
    
    def __unicode__(self):
        return u"%s: %s" % (str(self.flowcell), ', '.join([ str(s) for s in self.storage_devices.iterator() ]))

