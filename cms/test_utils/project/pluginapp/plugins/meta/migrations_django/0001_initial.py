# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='TestPluginModel2',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
                'db_table': 'meta_testpluginmodel2',
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='TestPluginModel4',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
                'db_table': 'or_another_4',
            },
            bases=('cms.cmsplugin',),
        ),
    ]
