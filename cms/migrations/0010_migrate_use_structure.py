# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from django.db import models, migrations


def forwards(apps, schema_editor):
    ph_model = apps.get_model('cms', 'Placeholder')
    page_model = apps.get_model('cms', 'Page')
    try:
        ph_ctype = ContentType.objects.get(app_label=ph_model._meta.app_label, model=ph_model._meta.model_name)
        page_ctype = ContentType.objects.get(app_label=page_model._meta.app_label, model=page_model._meta.model_name)
        permission, _ = Permission.objects.get_or_create(
            codename='use_structure', content_type=ph_ctype, name=u"Can use Structure mode")
        page_permission = Permission.objects.get(codename='change_page', content_type=page_ctype)
        for user in get_user_model().objects.filter(is_superuser=False, is_staff=True):
            if user.has_perm("cms.change_page"):
                user.user_permissions.add(permission)
        for group in Group.objects.all():
            if page_permission in group.permissions.all():
                group.permissions.add(permission)
    except ContentType.DoesNotExist:
        print(u'Users not migrated to use_structure permission, please add the permission manually')


def backwards(apps, schema_editor):
    ph_model = apps.get_model('cms', 'Placeholder')
    ph_ctype = ContentType.objects.get(app_label=ph_model._meta.app_label, model=ph_model._meta.model_name)
    permission, _ = Permission.objects.get_or_create(
        codename='use_structure', content_type=ph_ctype, name=u"Can use Structure mode")
    for user in get_user_model().objects.filter(is_superuser=False, is_staff=True):
        if user.has_perm("cms.use_structure"):
            user.user_permissions.remove(permission)
    for group in Group.objects.all():
        if permission in group.permissions.all():
            group.permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0008_auto_20150208_2149'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='placeholder',
            options={'permissions': (('use_structure', 'Can use Structure mode'),)},
        ),
        migrations.RunPython(forwards, backwards)
    ]
