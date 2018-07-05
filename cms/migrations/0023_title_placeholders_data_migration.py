# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings, os, sys

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

    # 1. Create a placeholder for each language the page is tied to (title_set)
    # 2. Move all plugins for each language into their respective placeholder
    # 3. Clean away the existing placeholders

    page_list = Page.objects.all().prefetch_related('title_set')

    for page in page_list:
        # Get all titles registered to the page
        title_set = page.title_set.all()
        # Get the pages placeholders
        placeholders = page.placeholders.all()
        # Add each placeholder on the page template to the title
        for title in title_set:
            # Get a list of the plugins attached to this placeholder for this language
            for placeholder in placeholders:
                # Get all of the plugins for this placeholder
                placeholder_plugins = Plugin.objects.filter(placeholder_id=placeholder.pk, language=title.language)
                # Clone the placeholder
                placeholder.pk = None
                placeholder.save()
                # Create a link to the new placeholder
                title.placeholders.add(placeholder)

                # Move the plugins to the relevant / new title -> placeholder
                for plugin in placeholder_plugins:
                    plugin.placeholder_id = placeholder.pk
                    plugin.save()

    # TODO: Delete previous placeholders!! None should have any plugins
    # TODO: Handle exceptions!!
    #except Exception:
    #    warnings.warn(u'Placeholder migration failure.')
    #raise os.sys.exit(u'Placeholder migration failure.')


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0022_title_placeholders'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
