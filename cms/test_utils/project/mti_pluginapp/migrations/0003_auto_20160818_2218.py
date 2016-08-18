# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0016_auto_20160608_1535'),
        ('mti_pluginapp', '0002_auto_20150112_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='NonPluginModel',
            fields=[
                ('other_id', models.AutoField(serialize=False, primary_key=True)),
                ('non_plugin', models.CharField(default=b'test non plugin', max_length=32, verbose_name=b'non plugin')),
            ],
        ),
        migrations.CreateModel(
            name='TestPluginGammaModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, related_name='mti_pluginapp_testplugingammamodel', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('abs', models.CharField(default=b'test plugin abs', max_length=32, verbose_name=b'abs')),
                ('gamma', models.CharField(default=b'test plugin gamma', max_length=32, verbose_name=b'gamma')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='ProxiedAlphaPluginModel',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mti_pluginapp.testpluginalphamodel',),
        ),
        migrations.CreateModel(
            name='ProxiedBetaPluginModel',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mti_pluginapp.testpluginbetamodel',),
        ),
        migrations.AlterField(
            model_name='testpluginalphamodel',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='mti_pluginapp_testpluginalphamodel', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.CreateModel(
            name='LessMixedPlugin',
            fields=[
                ('nonpluginmodel_ptr', models.OneToOneField(parent_link=True, auto_created=True, to='mti_pluginapp.NonPluginModel')),
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, related_name='mti_pluginapp_lessmixedplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('less_mixed', models.CharField(default=b'test plugin mixed', max_length=32, verbose_name=b'mixed')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin', 'mti_pluginapp.nonpluginmodel'),
        ),
        migrations.CreateModel(
            name='MixedPlugin',
            fields=[
                ('nonpluginmodel_ptr', models.OneToOneField(parent_link=True, auto_created=True, to='mti_pluginapp.NonPluginModel')),
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, related_name='mti_pluginapp_mixedplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('abs', models.CharField(default=b'test plugin abs', max_length=32, verbose_name=b'abs')),
                ('mixed', models.CharField(default=b'test plugin mixed', max_length=32, verbose_name=b'mixed')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin', 'mti_pluginapp.nonpluginmodel'),
        ),
    ]
