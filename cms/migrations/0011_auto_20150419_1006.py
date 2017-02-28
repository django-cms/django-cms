# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0010_migrate_use_structure'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='changed_by',
            field=models.CharField(verbose_name='changed by', max_length=255, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='created_by',
            field=models.CharField(verbose_name='created by', max_length=255, editable=False),
            preserve_default=True,
        ),
    ]
