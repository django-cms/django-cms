# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestPluginModel3',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='TestPluginModel5',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
                'db_table': 'or_another_5',
            },
            bases=('cms.cmsplugin',),
        ),
    ]
