# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessionAgency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('homepage', models.URLField(blank=True)),
                ('library_template', models.URLField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Accession Agencies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LibraryAccession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('accession', models.CharField(db_index=True, validators=[django.core.validators.RegexValidator('^[-A-Za-z0-9:.]*$', message='Please only use letters, digits, and :.-')], max_length=255)),
                ('url', models.URLField(blank=True, null=True)),
                ('created', models.DateTimeField()),
                ('agency', models.ForeignKey(to='samples.AccessionAgency', on_delete=models.CASCADE)),
                ('library', models.ForeignKey(to='samples.Library', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
