from __future__ import unicode_literals

from django.db import models

class LabelPrinter(models.Model):
    """
    Barcode Printer Information
    """
    name = models.CharField(max_length=256)
    model = models.CharField(max_length=64, default='ZM400')
    ip_address = models.GenericIPAddressField()
    labels = models.CharField(max_length=200)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return '%s: %s' % (self.name, self.labels)

class LabelTemplate(models.Model):
    """
    Maps templates to printer to use
    """
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    printer = models.ForeignKey(LabelPrinter, on_delete=models.CASCADE)
    
    ZPL_code = models.TextField('template')
    
    def __str__(self):
            return '%s %s' % (self.name, self.printer.name)

class LabelContent(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    subtitle = models.CharField(max_length=200, null=True, blank=True)
    text = models.CharField(max_length=200, null=True, blank=True)
    barcode = models.CharField(max_length=200, null=True, blank=True)
    template = models.ForeignKey(LabelTemplate, on_delete=models.CASCADE)
    creator = models.CharField(max_length=200)
