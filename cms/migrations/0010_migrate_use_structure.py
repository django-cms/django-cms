# -*- coding: utf-8 -*-
import warnings
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from django.conf import settings
from django.db import models, migrations


def forwards(apps, schema_editor):
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    ph_model = apps.get_model('cms', 'Placeholder')
    page_model = apps.get_model('cms', 'Page')
    try:
        ph_ctype = ContentType.objects.get_for_model(ph_model)
        page_ctype = ContentType.objects.get_for_model(page_model)
        permission, __ = Permission.objects.get_or_create(
            codename='use_structure', content_type=ph_ctype, name=u"Can use Structure mode")
        page_permission, __ = Permission.objects.get_or_create(
            codename='change_page', content_type=page_ctype, name=u'Can change page'
        )
        for user in user_model.objects.filter(is_superuser=False, is_staff=True):
            if user.user_permissions.filter(codename='change_page', content_type_id=page_ctype.pk).exists():
                user.user_permissions.add(permission.pk)
        for group in Group.objects.all():
            if page_permission in group.permissions.all():
                group.permissions.add(permission.pk)
    except Exception:
        warnings.warn(u'Users not migrated to use_structure permission, please add the permission manually')


def backwards(apps, schema_editor):
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    ph_model = apps.get_model('cms', 'Placeholder')
    ph_ctype = ContentType.objects.get(app_label=ph_model._meta.app_label, model=ph_model._meta.model_name)
    try:
        permission, __ = Permission.objects.get_or_create(
            codename='use_structure', content_type=ph_ctype, name=u"Can use Structure mode")
        for user in user_model.objects.filter(is_superuser=False, is_staff=True):
            user.user_permissions.remove(permission.pk)
        for group in Group.objects.all():
            if permission in group.permissions.all():
                group.permissions.remove(permission.pk)
    except Exception:
        warnings.warn(u'use_structure not removed from all the users, please check the permission manually')


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0009_merge'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='placeholder',
            options={'permissions': (('use_structure', 'Can use Structure mode'),)},
        ),
        migrations.RunPython(forwards, backwards)
    ]
