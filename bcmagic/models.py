from __future__ import unicode_literals

from django.db import models

#FIXME: Should be made more generic and probably pre-populated supported list
#   but for now, since we only have a ZM400, this will do.
PRINTER_MODELS=[ ('Zebra ZM400', 'Zebra ZM400'),
                 ('Zebra ZM600', 'Zebra ZM600')]

LABEL_SHAPES = [ ('Square', 'Square'), ('Circle', 'Circle') ]

class KeywordMap(models.Model):
    """
    Mapper object maps keyword|arg1|arg2|...|argN to REST urls
    """
    keyword = models.CharField(max_length=64)
    regex = models.CharField(max_length=1024)
    url_template = models.TextField()

class Printer(models.Model):
    """
    Barcode Printer Information
    """
    name = models.CharField(max_length=256)
    model = models.CharField(max_length=64, choices=PRINTER_MODELS)
    ip_address = models.IPAddressField()
    label_shape = models.CharField(max_length=32, choices=LABEL_SHAPES)
    label_width = models.FloatField(help_text='width or diameter in inches')
    label_height = models.FloatField(help_text='height in inches')
    notes = models.TextField()

    def __str__(self):
        return '%s, %s, %s, %s, %sx%s' % (self.name, self.model, self.ip_address, self.label_shape, self.label_width, self.label_width)
