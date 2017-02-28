# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('placeholderapp', '0002_charpksexample'),
    ]

    operations = [
        migrations.AddField(
            model_name='example1',
            name='publish',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
