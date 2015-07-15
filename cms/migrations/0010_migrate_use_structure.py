# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from django.conf import settings
from django.db import models, migrations


def forwards(apps, schema_editor):
    user_app_str, user_model_str = settings.AUTH_USER_MODEL.split('.', 1)
    user_model = apps.get_model(user_app_str, user_model_str)
    ph_model = apps.get_model('cms', 'Placeholder')
    page_model = apps.get_model('cms', 'Page')
    try:
        ph_ctype = ContentType.objects.get_for_model(ph_model)
        page_ctype = ContentType.objects.get_for_model(page_model)
        permission, _ = Permission.objects.get_or_create(
            codename='use_structure', content_type=ph_ctype, name=u"Can use Structure mode")
        page_permission = Permission.objects.get_or_create(codename='change_page', content_type=page_ctype)
        for user in user_model.objects.filter(is_superuser=False, is_staff=True):
            if user.has_perm("cms.change_page"):
                user.user_permissions.add(permission)
        for group in Group.objects.all():
            if page_permission in group.permissions.all():
                group.permissions.add(permission)
    except ContentType.DoesNotExist:
        print(u'Users not migrated to use_structure permission, please add the permission manually')


def backwards(apps, schema_editor):
    user_app_str, user_model_str = settings.AUTH_USER_MODEL.split('.', 1)
    user_model = apps.get_model(user_app_str, user_model_str)
    ph_model = apps.get_model('cms', 'Placeholder')
    ph_ctype = ContentType.objects.get(app_label=ph_model._meta.app_label, model=ph_model._meta.model_name)
    permission, _ = Permission.objects.get_or_create(
        codename='use_structure', content_type=ph_ctype, name=u"Can use Structure mode")
    for user in user_model.objects.filter(is_superuser=False, is_staff=True):
        if user.has_perm("cms.use_structure"):
            user.user_permissions.remove(permission)
    for group in Group.objects.all():
        if permission in group.permissions.all():
            group.permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0009_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='placeholder',
            options={'permissions': (('use_structure', 'Can use Structure mode'),)},
        ),
        migrations.RunPython(forwards, backwards)
    ]
