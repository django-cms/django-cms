# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('extensionapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mypageextension',
            name='favorite_users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
