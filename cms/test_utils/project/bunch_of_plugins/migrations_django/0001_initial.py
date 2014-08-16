# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.test_utils.project.bunch_of_plugins.models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestPlugin1',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='TestPlugin2',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(cms.test_utils.project.bunch_of_plugins.models.LeftMixin, 'cms.cmsplugin', cms.test_utils.project.bunch_of_plugins.models.RightMixin),
        ),
    ]
