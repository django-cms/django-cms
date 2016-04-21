# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import migrations, models


def forwards(apps, schema_editor):
    page_model = apps.get_model('cms', 'Page')
    page_ctype = ContentType.objects.get_for_model(page_model)
    Permission.objects.filter(
        name='',
        codename='change_page', content_type=page_ctype).update(name='Can change page')


def backwards(apps, schema_editor):
    # Do nothing, but allow backward migrations
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0013_urlconfrevision'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
