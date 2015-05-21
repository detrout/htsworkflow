# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def load_accession_agencies(apps, migrations):
    data = [
        {'name': 'ENCODE3', 'homepage': 'https://www.encodeproject.org',
         'library_template': 'https://www.encodeproject.org/libraries/{}/'},
        {'name': 'GEO', 'homepage': 'http://www.ncbi.nlm.nih.gov/geo/',
         'library_template':
         'http://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?&acc={}'},
    ]
    for record in data:
        Agency = apps.get_model('samples', 'AccessionAgency')
        o = Agency.objects.get_or_create(**record)


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0002_accessionagency_libraryaccession'),
    ]

    operations = [
        migrations.RunPython(load_accession_agencies)
    ]
