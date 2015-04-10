# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields
import cms.test_utils.project.placeholderapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_auto_20140816_1918'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicPlaceholderSlotExample',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('placeholder_1', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname=cms.test_utils.project.placeholderapp.models.dynamic_placeholder_1, related_name='dynamic_pl_1', editable=False)),
                ('placeholder_2', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname=cms.test_utils.project.placeholderapp.models.dynamic_placeholder_2, related_name='dynamic_pl_2', editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Example1',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('char_3', models.CharField(max_length=255, verbose_name='char_3')),
                ('char_4', models.CharField(max_length=255, verbose_name='char_4')),
                ('date_field', models.DateField(null=True)),
                ('placeholder', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname='placeholder', editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilingualExample1',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('placeholder_1', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname='placeholder_1', editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilingualExample1Translation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('language_code', models.CharField(db_index=True, max_length=15)),
                ('master', models.ForeignKey(null=True, to='placeholderapp.MultilingualExample1', related_name='translations', editable=False)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('char_3', models.CharField(max_length=255, verbose_name='char_3')),
                ('char_4', models.CharField(max_length=255, verbose_name='char_4')),
                ('placeholder_1', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname='placeholder_1', related_name='p1', editable=False)),
                ('placeholder_2', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname='placeholder_2', related_name='p2', editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
