# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0003_migrate_fcid_status'),
    ]

    operations = [
        migrations.RenameModel('DataRun', 'SequencingRun'),
        migrations.RenameField('datafile', 'data_run', 'sequencing_run'),
    ]
