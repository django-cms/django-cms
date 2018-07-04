# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings, os, sys

from django.db import migrations, models

"""
Title id 1
Title id 2
Page id 1
    Placeholder 1
        - Plugin 1 lang 1
        - Plugin 5 lang 2
    Placeholder 2
        - Plugin 3 lang 1
        - Plugin 4 lang 1

Title id 1
"""

def forwards(apps, schema_editor):

    Page = apps.get_model('cms', 'Page')
    # 1. Create a placeholder for each language the page is tied to (title_set)
    # 2. Move all plugins for each language into their respective placeholder
    page_list = Page.objects.all().prefetch_related('title_set')

    for page in page_list:
        # Get all titles registered to the page
        title_set = page.title_set.all()
        # Add each placeholder on the page template to the title
        for title in title_set:
            placeholders = page.placeholders.all()
            # FIXME: USE SET?????
            title.placeholders.add(*list(placeholders))

    #except Exception:
    #    warnings.warn(u'Placeholder migration failure.')

    #raise os.sys.exit(u'Placeholder migration failure.')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0022_title_placeholders'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
