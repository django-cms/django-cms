import warnings
import functools

from django.conf import settings
from django.db import models, migrations


def _get_manager(model, db_alias):
    return model.objects.db_manager(db_alias)


def forwards(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    get_manager = functools.partial(_get_manager, db_alias=db_alias)

    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    ph_model = apps.get_model('cms', 'Placeholder')
    page_model = apps.get_model('cms', 'Page')

    try:
        ph_ctype = get_manager(ContentType).get_for_model(ph_model)
        page_ctype = get_manager(ContentType).get_for_model(page_model)
        permission, __ = get_manager(Permission).get_or_create(
            codename='use_structure', content_type=ph_ctype, name="Can use Structure mode")
        page_permission, __ = get_manager(Permission).get_or_create(
            codename='change_page', content_type=page_ctype, name='Can change page'
        )
        for user in get_manager(user_model).filter(is_superuser=False, is_staff=True):
            if user.user_permissions.filter(codename='change_page', content_type_id=page_ctype.pk).exists():
                user.user_permissions.add(permission.pk)
        for group in get_manager(Group).all():
            if page_permission in group.permissions.all():
                group.permissions.add(permission.pk)
    except Exception:
        warnings.warn('Users not migrated to use_structure permission, please add the permission manually')


def backwards(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    get_manager = functools.partial(_get_manager, db_alias=db_alias)

    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    ph_model = apps.get_model('cms', 'Placeholder')
    ph_ctype = get_manager(ContentType).get(
        app_label=ph_model._meta.app_label,
        model=ph_model._meta.model_name,
    )

    try:
        permission, __ = get_manager(Permission).get_or_create(
            codename='use_structure', content_type=ph_ctype, name="Can use Structure mode")
        for user in get_manager(user_model).filter(is_superuser=False, is_staff=True):
            user.user_permissions.remove(permission.pk)
        for group in get_manager(Group).all():
            if permission in group.permissions.all():
                group.permissions.remove(permission.pk)
    except Exception:
        warnings.warn('use_structure not removed from all the users, please check the permission manually')


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0009_merge'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='placeholder',
            options={'permissions': (('use_structure', 'Can use Structure mode'),)},
        ),
        migrations.RunPython(forwards, backwards)
    ]
