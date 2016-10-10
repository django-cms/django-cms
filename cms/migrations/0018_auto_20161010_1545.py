# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0017_cmsplugin_cmsplugin_hidden'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cmsplugin',
            name='cmsplugin_hidden',
            field=models.BooleanField(editable=False, default=False, verbose_name='Hide plugin contents'),
        ),
    ]
