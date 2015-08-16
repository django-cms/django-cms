# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_auto_20150419_1006'),
        ('sampleapp', '0002_auto_20141015_1057'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('link', cms.models.fields.PageField(related_name='plugin_link_link', to='cms.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
