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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('test_file', models.FileField(blank=True, null=True, upload_to='fileapp/')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
