# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_auto_20150419_1006'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='pageuser',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AlterField(
            model_name='globalpagepermission',
            name='sites',
            field=models.ManyToManyField(blank=True, to='sites.Site', verbose_name='sites', help_text='If none selected, user haves granted permissions to all sites.'),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, editable=False, related_name='djangocms_usersettings'),
        ),
    ]
