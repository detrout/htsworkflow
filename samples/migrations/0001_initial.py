# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Affiliation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='Name', db_index=True, max_length=256)),
                ('contact', models.CharField(blank=True, null=True, max_length=256, verbose_name='Lab Name')),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
            ],
            options={
                'ordering': ['name', 'contact'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Antibody',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('antigene', models.CharField(max_length=500, db_index=True)),
                ('nickname', models.CharField(db_index=True, max_length=20, null=True, blank=True)),
                ('catalog', models.CharField(max_length=50, null=True, blank=True)),
                ('antibodies', models.CharField(max_length=500, db_index=True)),
                ('source', models.CharField(db_index=True, max_length=500, null=True, blank=True)),
                ('biology', models.TextField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['antigene'],
                'verbose_name_plural': 'antibodies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Cellline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cellline_name', models.CharField(unique=True, max_length=100, db_index=True)),
                ('nickname', models.CharField(db_index=True, max_length=20, null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['cellline_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('condition_name', models.CharField(unique=True, max_length=2000, db_index=True)),
                ('nickname', models.CharField(db_index=True, max_length=20, null=True, verbose_name='Short Name', blank=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['condition_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperimentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HTSUser',
            fields=[
                ('user_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['first_name', 'last_name', 'username'],
            },
            bases=('auth.user',),
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('library_name', models.CharField(unique=True, max_length=100)),
                ('hidden', models.BooleanField(default=False)),
                ('account_number', models.CharField(max_length=100, null=True, blank=True)),
                ('replicate', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)])),
                ('multiplex_id', models.CharField(max_length=255, null=True, verbose_name='Index ID', blank=True)),
                ('creation_date', models.DateField(null=True, blank=True)),
                ('made_for', models.CharField(max_length=50, verbose_name='ChIP/DNA/RNA Made By', blank=True)),
                ('made_by', models.CharField(default='Lorian', max_length=50, blank=True)),
                ('stopping_point', models.CharField(default='Done', max_length=25, choices=[('?', 'Unknown'), ('Sample', 'Raw sample'), ('Progress', 'In progress'), ('1A', 'Ligation, then gel'), ('PCR', 'Ligation, then PCR'), ('1Ab', 'Ligation, PCR, then gel'), ('1Ac', 'Ligation, gel, then 12x PCR'), ('1Aa', 'Ligation, gel, then 18x PCR'), ('2A', 'Ligation, PCR, gel, PCR'), ('Done', 'Completed')])),
                ('undiluted_concentration', models.DecimalField(decimal_places=2, max_digits=5, blank=True, help_text='Undiluted concentration (ng/\xb5l)', null=True, verbose_name='Concentration')),
                ('successful_pM', models.DecimalField(null=True, max_digits=9, decimal_places=1, blank=True)),
                ('ten_nM_dilution', models.BooleanField(default=False)),
                ('gel_cut_size', models.IntegerField(default=225, null=True, blank=True)),
                ('insert_size', models.IntegerField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('bioanalyzer_summary', models.TextField(default='', blank=True)),
                ('bioanalyzer_concentration', models.DecimalField(help_text='(ng/\xb5l)', null=True, max_digits=5, decimal_places=2, blank=True)),
                ('bioanalyzer_image_url', models.URLField(default='', blank=True)),
                ('affiliations', models.ManyToManyField(related_name='library_affiliations', null=True, to='samples.Affiliation')),
                ('amplified_from_sample', models.ForeignKey(related_name='amplified_into_sample', blank=True, to='samples.Library', null=True)),
                ('antibody', models.ForeignKey(blank=True, to='samples.Antibody', null=True)),
                ('cell_line', models.ForeignKey(verbose_name='Background', blank=True, to='samples.Cellline', null=True)),
                ('condition', models.ForeignKey(blank=True, to='samples.Condition', null=True)),
                ('experiment_type', models.ForeignKey(to='samples.ExperimentType')),
            ],
            options={
                'ordering': ['-id'],
                'verbose_name_plural': 'libraries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LibraryType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='Adapter Type')),
                ('is_paired_end', models.BooleanField(default=True, help_text='can you do a paired end run with this adapter')),
                ('can_multiplex', models.BooleanField(default=True, help_text='Does this adapter provide multiplexing?')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiplexIndex',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('multiplex_id', models.CharField(max_length=6)),
                ('sequence', models.CharField(max_length=12, null=True, blank=True)),
                ('adapter_type', models.ForeignKey(to='samples.LibraryType')),
            ],
            options={
                'verbose_name_plural': 'multiplex indicies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scientific_name', models.CharField(max_length=256, db_index=True)),
                ('common_name', models.CharField(max_length=256, blank=True)),
            ],
            options={
                'ordering': ['scientific_name'],
                'verbose_name_plural': 'species',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag_name', models.CharField(max_length=100, db_index=True)),
                ('context', models.CharField(default='Library', max_length=50, choices=[('Library', 'Library'), ('ANY', 'ANY')])),
            ],
            options={
                'ordering': ['context', 'tag_name'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='multiplexindex',
            unique_together=set([('adapter_type', 'multiplex_id')]),
        ),
        migrations.AddField(
            model_name='library',
            name='library_species',
            field=models.ForeignKey(to='samples.Species'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='library',
            name='library_type',
            field=models.ForeignKey(verbose_name='Adapter Type', blank=True, to='samples.LibraryType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='library',
            name='tags',
            field=models.ManyToManyField(related_name='library_tags', null=True, to='samples.Tag', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='affiliation',
            name='users',
            field=models.ManyToManyField(to='samples.HTSUser', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='affiliation',
            unique_together=set([('name', 'contact')]),
        ),
    ]
