# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0016_auto_20160608_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='cmsplugin',
            name='cmsplugin_hidden',
            field=models.BooleanField(default=False, verbose_name=b'Hide plugin contents'),
        ),
    ]
