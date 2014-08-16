# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('description', cms.models.fields.PlaceholderField(editable=False, to='cms.Placeholder', null=True, slotname='category_description')),
                ('parent', models.ForeignKey(blank=True, to='sampleapp.Category', null=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to='pictures')),
                ('category', models.ForeignKey(to='sampleapp.Category')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
