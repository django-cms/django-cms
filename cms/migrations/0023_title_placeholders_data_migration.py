# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings, os, sys

from django.db import migrations, models


def forwards(apps, schema_editor):

    Placeholder = apps.get_model('cms', 'Placeholder')
    Plugin = apps.get_model('cms', 'CMSPlugin')
    Page = apps.get_model('cms', 'Page')
    Title = apps.get_model('cms', 'Title')

    # 1. Create a placeholder for each language the page is tied to (title_set)
    # 2. Move all plugins for each language into their respective placeholder

    page_list = Page.objects.all().prefetch_related('title_set')

    page_count = page_list.count()

    for page in page_list:

        # Add each placeholder to the title / language
        # Get all titles registered to the page
        title_set = page.title_set.all()
        # For each title add the placeholders
        for title in title_set:

            title.placeholders.add(page.placeholders.all())


    """
    # for each page language
    for page_title in page.title_set:
        new_title = page_title
    """




    #except Exception:
    #    warnings.warn(u'Placeholder migration failure.')

    raise os.sys.exit(u'Placeholder migration failure.')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0022_title_placeholders'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
