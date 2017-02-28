# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0007_auto_20141028_1559'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('reverse_id', 'site', 'publisher_is_draft'), ('publisher_is_draft', 'site', 'application_namespace')]),
        ),
    ]
