# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_auto_20140926_2347'),
        ('placeholderapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharPksExample',
            fields=[
                ('char_1', models.CharField(max_length=255, verbose_name='char_1')),
                ('slug', models.SlugField(max_length=255, serialize=False, verbose_name='char_1', primary_key=True)),
                ('placeholder_1', cms.models.fields.PlaceholderField(related_name='charpk_p1', slotname='placeholder_1', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
