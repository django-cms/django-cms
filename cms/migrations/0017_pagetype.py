# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def update_descendants(parent, **data):
    parent.children.update(**data)

    for child in parent.children.iterator():
        update_descendants(child, **data)


def migrate_to_page_types(apps, schema_editor):
    Page = apps.get_model('cms', 'Page')
    db_alias = schema_editor.connection.alias

    try:
        page_types_root = Page.objects.using(db_alias).get(
            publisher_is_draft=True,
            reverse_id='page_types',
        )
    except Page.DoesNotExist:
        return

    update_descendants(page_types_root, is_page_type=True)

    # Remove reverse id from draft page
    page_types_root.reverse_id = ''
    page_types_root.is_page_type = True
    page_types_root.save(update_fields=['reverse_id', 'is_page_type'])
    page_types_root_public = page_types_root.publisher_public

    if page_types_root_public:
        # very strange case.. technically page-types should never be published.
        # but nothing actually prevents it, so update public pages (if any).
        update_descendants(page_types_root_public, is_page_type=True)

        # Remove reverse id from public page
        page_types_root_public.reverse_id = ''
        page_types_root_public.is_page_type = True
        page_types_root_public.save(update_fields=['reverse_id', 'is_page_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0016_auto_20160608_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='is_page_type',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='PageType',
            fields=[
            ],
            options={
                'default_permissions': [],
                'proxy': True,
            },
            bases=('cms.page',),
        ),
        migrations.RunPython(migrate_to_page_types, migrations.RunPython.noop),
    ]
