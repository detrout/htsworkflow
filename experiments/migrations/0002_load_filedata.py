# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def initialize_file_type(apps, migrations):
    data = [
        ('run_xml', 'application/vnd.htsworkflow-run-xml', 'run.*\\.xml\\Z(?ms)'),
        ('Summary.htm', 'text/html', 'Summary\\.htm\\Z(?ms)'),
        ('IVC All', 'image/png', 's_(?P<lane>[0-9])_all\\.png\\Z(?ms)'),
        ('IVC Call', 'image/png', 's_(?P<lane>[0-9])_call\\.png\\Z(?ms)'),
        ('IVC Percent All', 'image/png', 's_(?P<lane>[0-9])_percent_all\\.png\\Z(?ms)'),
        ('IVC Percent Base', 'image/png', 's_(?P<lane>[0-9])_percent_base\\.png\\Z(?ms)'),
        ('IVC Percent Call', 'image/png', 's_(?P<lane>[0-9])_percent_call\\.png\\Z(?ms)'),
        ('GERALD Scores', None, 's_(?P<lane>[0-9])_percent_call\\.png\\Z(?ms)'),
        ('ELAND Result', 'chemical/seq-na-eland',
         's_(?P<lane>[0-9])((?P<end>[1-4])_)?_eland_result\\.txt\\.bz2\\Z(?ms)'),
        ('ELAND Multi', 'chemical/seq-na/eland',
         's_(?P<lane>[0-9])((?P<end>[1-4])_)?_eland_multi\\.txt\\.bz2\\Z(?ms)'),
        ('ELAND Extended', 'chemical/seq-na-eland',
         's_(?P<lane>[0-9])((?P<end>[1-4])_)?_eland_extended\\.txt\\.bz2\\Z(?ms)'),
        ('ELAND Export', 'chemical/seq-na-eland',
         's_(?P<lane>[0-9])((?P<end>[1-4])_)?_export\\.txt\\.bz2\\Z(?ms)'),
        ('SRF', 'chemical/seq-na/eland', '.*_(?P<lane>[1-8])\\.srf\\Z(?ms)'),
        ('QSEQ tarfile', 'chemical/seq-na-qseq',
         '.*_l(?P<lane>[1-8])_r(?P<end>[1-4])\\.tar\\.bz2\\Z(?ms)'),
        ('HiSeq Fastq', 'chemical/seq-na-fastq',
         '(?P<library>[0-9]+)_(NoIndex|[AGCT]+)_L(?P<lane>[0-9]+)_R(?P<end>[12])_(?P<split>[0-9]+)\\.fastq\\.gz'),

        # Keep listing off patterns to always load into the database.
    ]
    for name, mimetype, regex in data:
        record = {'name': name,
                  'mimetype': mimetype,
                  'regex': regex}
        FileType = apps.get_model('experiments', 'FileType')
        o = FileType.objects.get_or_create(**record)
        

class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initialize_file_type)
    ]
