# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('content', models.TextField(default='', max_length=255, verbose_name='Banner content')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
            ],
        ),
    ]
