# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0006_auto_20140924_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='path',
            field=models.CharField(max_length=255, unique=True),
            preserve_default=True,
        ),
    ]
