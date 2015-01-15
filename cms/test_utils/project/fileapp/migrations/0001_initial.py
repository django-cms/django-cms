# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileModel',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('test_file', models.FileField(null=True, blank=True, upload_to='fileapp/')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
