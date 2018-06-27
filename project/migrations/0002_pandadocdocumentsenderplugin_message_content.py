# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pandadocdocumentsenderplugin',
            name='message_content',
            field=models.TextField(default='Please sign this document. Thanks', verbose_name='Content for signing email'),
            preserve_default=False,
        ),
    ]
