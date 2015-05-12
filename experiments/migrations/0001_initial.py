# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import experiments.models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClusterStation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('isdefault', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-isdefault', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('random_key', models.CharField(default=experiments.models.str_uuid, max_length=64, db_index=True)),
                ('relative_pathname', models.CharField(max_length=255, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('runfolder_name', models.CharField(max_length=50)),
                ('result_dir', models.CharField(max_length=255)),
                ('last_update_time', models.DateTimeField()),
                ('run_start_time', models.DateTimeField()),
                ('cycle_start', models.IntegerField(null=True, blank=True)),
                ('cycle_stop', models.IntegerField(null=True, blank=True)),
                ('run_status', models.IntegerField(blank=True, null=True, choices=[(0, 'Sequencer running'), (1, 'Data Pipeline Started'), (2, 'Data Pipeline Interrupted'), (3, 'Data Pipeline Finished'), (4, 'Collect Results Started'), (5, 'Collect Results Finished'), (6, 'QC Started'), (7, 'QC Finished'), (255, 'DONE')])),
                ('image_software', models.CharField(max_length=50)),
                ('image_version', models.CharField(max_length=50)),
                ('basecall_software', models.CharField(max_length=50)),
                ('basecall_version', models.CharField(max_length=50)),
                ('alignment_software', models.CharField(max_length=50)),
                ('alignment_version', models.CharField(max_length=50)),
                ('comment', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('mimetype', models.CharField(max_length=50, null=True, blank=True)),
                ('regex', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FlowCell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flowcell_id', models.CharField(unique=True, max_length=20, db_index=True)),
                ('run_date', models.DateTimeField()),
                ('advanced_run', models.BooleanField(default=False)),
                ('paired_end', models.BooleanField(default=False)),
                ('read_length', models.IntegerField(default=32)),
                ('control_lane', models.IntegerField(blank=True, null=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (0, 'All Lanes')])),
                ('notes', models.TextField(blank=True)),
                ('cluster_station', models.ForeignKey(default=experiments.models.cluster_station_default, to='experiments.ClusterStation')),
            ],
            options={
                'ordering': ['-run_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Lane',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lane_number', models.IntegerField()),
                ('pM', models.DecimalField(default=5, max_digits=5, decimal_places=2)),
                ('cluster_estimate', models.IntegerField(null=True, blank=True)),
                ('status', models.IntegerField(blank=True, null=True, choices=[(0, 'Failed'), (1, 'Marginal'), (2, 'Good'), (100, 'Not run')])),
                ('comment', models.TextField(null=True, blank=True)),
                ('flowcell', models.ForeignKey(to='experiments.FlowCell')),
                ('library', models.ForeignKey(to='samples.Library')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sequencer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, db_index=True)),
                ('instrument_name', models.CharField(max_length=50, db_index=True)),
                ('serial_number', models.CharField(max_length=50, db_index=True)),
                ('model', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('isdefault', models.BooleanField(default=False)),
                ('comment', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['-isdefault', '-active', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='flowcell',
            name='sequencer',
            field=models.ForeignKey(default=experiments.models.sequencer_default, to='experiments.Sequencer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datarun',
            name='flowcell',
            field=models.ForeignKey(verbose_name='Flowcell Id', to='experiments.FlowCell'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafile',
            name='data_run',
            field=models.ForeignKey(to='experiments.DataRun'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafile',
            name='file_type',
            field=models.ForeignKey(to='experiments.FileType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafile',
            name='library',
            field=models.ForeignKey(blank=True, to='samples.Library', null=True),
            preserve_default=True,
        ),
    ]
