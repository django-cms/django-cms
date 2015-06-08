# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('placeholderapp', '0003_example1_publish'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='multilingualexample1translation',
            options={'managed': True},
        ),
    ]
