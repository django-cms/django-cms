# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0013_urlconfrevision'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cmsplugin',
            name='position',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='position', editable=False),
        ),
    ]
