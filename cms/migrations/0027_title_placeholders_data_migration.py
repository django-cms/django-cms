from __future__ import unicode_literals
from collections import defaultdict
import warnings

from django.db import migrations, models

"""
# Current / Previous Placeholder structure
Title id 1
Title id 2
Page id 1
    - Placeholder 1
        - Plugin 1 lang 1
        - Plugin 5 lang 2
    - Placeholder 2
        - Plugin 3 lang 1
        - Plugin 4 lang 1

# New Title Placeholder structure
Page 1
    - Title id 1
        - Placeholder 1
            - Plugin 1 lang 1
        - Placeholder 2
            - Plugin 3 lang 1
            - Plugin 4 lang 1
    - Title id 2
        - Placeholder 1
            - Plugin 5 lang 2
"""


def forwards(apps, schema_editor):
    Page = apps.get_model('cms', 'Page')
    Plugin = apps.get_model('cms', 'CMSPlugin')
    Placeholder = apps.get_model('cms', 'Placeholder')
    db_alias = schema_editor.connection.alias
    cms_pages = (
        Page
        .objects
        .using(db_alias)
        .filter(placeholders__isnull=False)
        .distinct()
        .prefetch_related('placeholders', 'title_set')
    )
    new_placeholders = []
    old_placeholder_ids = []

    for page in cms_pages:
        for title in page.title_set.all():
            for placeholder in page.placeholders.all():
                new_placeholder = Placeholder(
                    slot=placeholder.slot,
                    default_width=placeholder.default_width,
                    title_id=title.pk,
                )
                new_placeholders.append(new_placeholder)
                old_placeholder_ids.append(placeholder.pk)

    # Create all new placeholders
    Placeholder.objects.using(db_alias).bulk_create(new_placeholders)

    # Map out all new placeholders by title id
    placeholders_by_title = defaultdict(list)
    new_placeholder_lookup = (
        Placeholder
        .objects
        .using(db_alias)
        .filter(title_id__isnull=False)
    )

    for new_pl in new_placeholder_lookup.iterator():
        placeholders_by_title[new_pl.title_id].append(new_pl)

    for page in cms_pages:
        for translation in page.title_set.all():
            new_placeholders = placeholders_by_title[translation.pk]

            for new_placeholder in new_placeholders:
                # Move all plugins whose language matches
                # the current translation and are hosted on the
                # current placeholder slot to point to the new title placeholder.
                Plugin.objects.filter(
                    language=translation.language,
                    placeholder__page=page,
                    placeholder__slot=new_placeholder.slot,
                ).update(placeholder_id=new_placeholder.pk)
            # Attach the new placeholders to the title
            translation.placeholders.set(new_placeholders)

    # Gather the old placeholders
    old_placeholders = (
        Placeholder
        .objects
        .using(db_alias)
        .filter(pk__in=old_placeholder_ids)
        .annotate(plugin_count=models.Count('cmsplugin'))
    )

    if old_placeholders.filter(plugin_count__gt=0).exists():
        warnings.warn(
            "There's placeholders in your database "
            "with plugins in a language that's not configured "
            "These placeholders and its plugins are not in use and can be removed.",
            UserWarning,
        )

    # Delete all old placeholders that have no plugins
    old_placeholders.filter(plugin_count=0).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0026_title_placeholders'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
