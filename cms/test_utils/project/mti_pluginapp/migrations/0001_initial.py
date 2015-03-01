# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_auto_20140926_2347'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestPluginAlphaModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('alpha', models.CharField(default=b'test plugin alpha', max_length=32, verbose_name=b'name')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='TestPluginBetaModel',
            fields=[
                ('testpluginalphamodel_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='mti_pluginapp.TestPluginAlphaModel')),
                ('beta', models.CharField(default=b'test plugin beta', max_length=32, verbose_name=b'name')),
            ],
            options={
                'abstract': False,
            },
            bases=('mti_pluginapp.testpluginalphamodel',),
        ),
    ]
