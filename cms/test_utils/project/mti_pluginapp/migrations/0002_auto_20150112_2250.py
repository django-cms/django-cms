# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mti_pluginapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testpluginalphamodel',
            name='alpha',
            field=models.CharField(max_length=32, default='test plugin alpha', verbose_name='name'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='testpluginbetamodel',
            name='beta',
            field=models.CharField(max_length=32, default='test plugin beta', verbose_name='name'),
            preserve_default=True,
        ),
    ]
