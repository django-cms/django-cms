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
            name='MainModel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Translations',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('language_code', models.CharField(db_index=True, max_length=15)),
                ('master', models.ForeignKey(to='fakemlng.MainModel')),
                ('placeholder', cms.models.fields.PlaceholderField(editable=False, to='cms.Placeholder', null=True, slotname='translated')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='translations',
            unique_together=set([('master', 'language_code')]),
        ),
    ]
