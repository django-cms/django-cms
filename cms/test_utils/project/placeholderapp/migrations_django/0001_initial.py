# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.test_utils.project.placeholderapp.models
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicPlaceholderSlotExample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('placeholder_1', cms.models.fields.PlaceholderField(slotname=cms.test_utils.project.placeholderapp.models.dynamic_placeholder_1, editable=False, to='cms.Placeholder', null=True)),
                ('placeholder_2', cms.models.fields.PlaceholderField(slotname=cms.test_utils.project.placeholderapp.models.dynamic_placeholder_2, editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Example1',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('char_3', models.CharField(max_length=255, verbose_name='char_3')),
                ('char_4', models.CharField(max_length=255, verbose_name='char_4')),
                ('date_field', models.DateField(null=True)),
                ('placeholder', cms.models.fields.PlaceholderField(slotname=b'placeholder', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilingualExample1',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('placeholder_1', cms.models.fields.PlaceholderField(slotname=b'placeholder_1', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilingualExample1Translation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('language_code', models.CharField(max_length=15, db_index=True)),
                ('master', models.ForeignKey(editable=False, to='placeholderapp.MultilingualExample1', null=True)),
            ],
            options={
                'db_table': 'placeholderapp_multilingualexample1_translation',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='multilingualexample1translation',
            unique_together=set([(b'language_code', b'master')]),
        ),
        migrations.CreateModel(
            name='TwoPlaceholderExample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('char_2', models.CharField(max_length=255, verbose_name='char_2')),
                ('char_3', models.CharField(max_length=255, verbose_name='char_3')),
                ('char_4', models.CharField(max_length=255, verbose_name='char_4')),
                ('placeholder_1', cms.models.fields.PlaceholderField(slotname=b'placeholder_1', editable=False, to='cms.Placeholder', null=True)),
                ('placeholder_2', cms.models.fields.PlaceholderField(slotname=b'placeholder_2', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
