# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emailuserapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailuser',
            name='email',
            field=models.EmailField(help_text=b'Required.  Standard format email address.', unique=True, max_length=300, verbose_name=b'email address', blank=True),
            preserve_default=True,
        ),
    ]
