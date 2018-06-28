# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings, os

from django.db import migrations, models


def forwards(apps, schema_editor):

    placeholder_model = apps.get_model('cms', 'Placeholder')
    page_model = apps.get_model('cms', 'Page')
    title_model = apps.get_model('cms', 'Title')

    try:
        # 1. Create a placeholder for each language the page is tied to (title_set)
        title_list = title_model.objects.all()
        page_list = page_model.objects.all()

        page_count = page_list.count()

        for page in page_list:
            title_set_count = page.title_set

        """
            # for each page language
            for page_title in page.title_set:
                new_title = page_title
        """

        # 2. Move all plugins for each language into their respective placeholder


    except Exception:
        warnings.warn(u'Placeholder migration failure.')

    raise os.sys.exit(u'Placeholder migration failure.')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0021_auto_20180507_1432'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]

    """
    migrations.AddField(
        model_name='title',
        name='placeholders',
        field=models.ManyToManyField(editable=False, to='cms.Placeholder'),
    ),
    """


