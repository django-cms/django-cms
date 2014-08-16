# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields
import cms.test_utils.project.placeholderapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicPlaceholderSlotExample',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('char_1', models.CharField(verbose_name='char_1', max_length=255)),
                ('char_2', models.CharField(verbose_name='char_2', max_length=255)),
                ('placeholder_1', cms.models.fields.PlaceholderField(related_name='dynamic_pl_1', editable=False, to='cms.Placeholder', null=True, slotname=cms.test_utils.project.placeholderapp.models.dynamic_placeholder_1)),
                ('placeholder_2', cms.models.fields.PlaceholderField(related_name='dynamic_pl_2', editable=False, to='cms.Placeholder', null=True, slotname=cms.test_utils.project.placeholderapp.models.dynamic_placeholder_2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Example1',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('char_1', models.CharField(verbose_name='char_1', max_length=255)),
                ('char_2', models.CharField(verbose_name='char_2', max_length=255)),
                ('char_3', models.CharField(verbose_name='char_3', max_length=255)),
                ('char_4', models.CharField(verbose_name='char_4', max_length=255)),
                ('date_field', models.DateField(null=True)),
                ('placeholder', cms.models.fields.PlaceholderField(editable=False, to='cms.Placeholder', null=True, slotname='placeholder')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilingualExample1',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('placeholder_1', cms.models.fields.PlaceholderField(editable=False, to='cms.Placeholder', null=True, slotname='placeholder_1')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilingualExample1Translation',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('char_1', models.CharField(verbose_name='char_1', max_length=255)),
                ('char_2', models.CharField(verbose_name='char_2', max_length=255)),
                ('language_code', models.CharField(db_index=True, max_length=15)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='placeholderapp.MultilingualExample1', null=True)),
            ],
            options={
                'db_table': 'placeholderapp_multilingualexample1_translation',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='multilingualexample1translation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.CreateModel(
            name='TwoPlaceholderExample',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('char_1', models.CharField(verbose_name='char_1', max_length=255)),
                ('char_2', models.CharField(verbose_name='char_2', max_length=255)),
                ('char_3', models.CharField(verbose_name='char_3', max_length=255)),
                ('char_4', models.CharField(verbose_name='char_4', max_length=255)),
                ('placeholder_1', cms.models.fields.PlaceholderField(related_name='p1', editable=False, to='cms.Placeholder', null=True, slotname='placeholder_1')),
                ('placeholder_2', cms.models.fields.PlaceholderField(related_name='p2', editable=False, to='cms.Placeholder', null=True, slotname='placeholder_2')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
