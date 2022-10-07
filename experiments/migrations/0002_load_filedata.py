# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def initialize_file_type(apps, migrations):
    data = [
        ('run_xml', 'application/vnd.htsworkflow-run-xml', '(?ms)run.*\\.xml\\Z'),
        ('Summary.htm', 'text/html', '(?ms)Summary\\.htm\\Z'),
        ('IVC All', 'image/png', '(?ms)s_(?P<lane>[0-9])_all\\.png\\Z'),
        ('IVC Call', 'image/png', '(?ms)s_(?P<lane>[0-9])_call\\.png\\Z'),
        ('IVC Percent All', 'image/png', '(?ms)s_(?P<lane>[0-9])_percent_all\\.png\\Z'),
        ('IVC Percent Base', 'image/png', '(?ms)s_(?P<lane>[0-9])_percent_base\\.png\\Z'),
        ('IVC Percent Call', 'image/png', '(?ms)s_(?P<lane>[0-9])_percent_call\\.png\\Z'),
        ('GERALD Scores', None, '(?ms)s_(?P<lane>[0-9])_percent_call\\.png\\Z'),
        ('ELAND Result', 'chemical/seq-na-eland',
         '(?ms)s_(?P<lane>[0-9])((?P<end>[1-4])_)?_eland_result\\.txt\\.bz2\\Z'),
        ('ELAND Multi', 'chemical/seq-na/eland',
         '(?ms)s_(?P<lane>[0-9])((?P<end>[1-4])_)?_eland_multi\\.txt\\.bz2\\Z'),
        ('ELAND Extended', 'chemical/seq-na-eland',
         '(?ms)s_(?P<lane>[0-9])((?P<end>[1-4])_)?_eland_extended\\.txt\\.bz2\\Z'),
        ('ELAND Export', 'chemical/seq-na-eland',
         '(?ms)s_(?P<lane>[0-9])((?P<end>[1-4])_)?_export\\.txt\\.bz2\\Z'),
        ('SRF', 'chemical/seq-na/eland', '(?ms).*_(?P<lane>[1-8])\\.srf\\Z'),
        ('QSEQ tarfile', 'chemical/seq-na-qseq',
         '(?ms).*_l(?P<lane>[1-8])_r(?P<end>[1-4])\\.tar\\.bz2\\Z'),
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
