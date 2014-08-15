# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='MainModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Translations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, db_index=True)),
                ('master', models.ForeignKey(to='fakemlng.MainModel')),
                ('placeholder', cms.models.fields.PlaceholderField(slotname=b'translated', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='translations',
            unique_together=set([(b'master', b'language_code')]),
        ),
    ]
