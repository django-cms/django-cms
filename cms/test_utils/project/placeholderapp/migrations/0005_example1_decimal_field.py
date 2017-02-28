# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('placeholderapp', '0004_auto_20150503_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='example1',
            name='decimal_field',
            field=models.DecimalField(null=True, max_digits=5, decimal_places=1, blank=True),
            preserve_default=True,
        ),
    ]
