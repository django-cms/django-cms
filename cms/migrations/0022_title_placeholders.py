# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings

from django.db import migrations, models


def forwards(apps, schema_editor):

    placeholder_model = apps.get_model('cms', 'Placeholder')
    page_model = apps.get_model('cms', 'Page')
    title_model = apps.get_model('cms', 'Title')

    try:
        # 1. Create a placeholder for each language the page is tied to (title_set)
        title_list = title_model.objects.all()
        page_list = page_model.objects.all()

        """

        for each page language


        """
        # 2. Move all plugins for each language into their respective placeholder

        raise Exception

    except Exception:
        warnings.warn(u'Placeholder migration failure.')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0021_auto_20180507_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='title',
            name='placeholders',
            field=models.ManyToManyField(editable=False, to='cms.Placeholder'),
        ),
        migrations.RunPython(forwards, backwards)
    ]
