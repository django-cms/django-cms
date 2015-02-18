# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model

from django.db import models, migrations


def forwards(apps, schema_editor):
    ph_model = apps.get_model('cms', 'Placeholder')
    ctype = apps.get_model('contenttypes', 'ContentType')
    ph_ctype = ctype.objects.get(app_label=ph_model._meta.app_label, model=ph_model._meta.model_name)
    permission, _ = apps.get_model('auth', 'Permission').objects.get_or_create(codename='use_structure', defaults={
        'codename': 'use_structure',
        'name': "Can use Structure mode",
        'content_type': ph_ctype
    })
    for user in get_user_model().objects.filter(is_superuser=False, is_staff=True):
        if user.has_perm("cms.can_change_page"):
            user.user_permissions.add(permission)


def backwards(apps, schema_editor):
    ph_model = apps.get_model('cms', 'Placeholder')
    ph_model = apps.get_model('cms', 'Placeholder')
    ctype = apps.get_model('contenttypes', 'ContentType')
    ph_ctype = ctype.objects.get(app_label=ph_model._meta.app_label, model=ph_model._meta.model_name)
    permission, _ = apps.get_model('auth', 'Permission').objects.get_or_create(codename='use_structure', defaults={
        'codename': 'use_structure',
        'name': "Can use Structure mode",
        'content_type': ph_ctype
    })
    for user in get_user_model().objects.filter(is_superuser=False, is_staff=True):
        if user.has_perm("cms.use_structure"):
            user.user_permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0008_auto_20150208_2149'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
