# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_auto_20140926_2347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='template',
            field=models.CharField(default=b'INHERIT', help_text='The template used to render the content.', max_length=100, verbose_name='template', choices=[(b'fullwidth.html', 'Fullwidth'), (b'sidebar_left.html', 'Sidebar Left'), (b'sidebar_right.html', 'Sidebar Right'), (b'basepage.html', 'Base Page'), (b'homepage.html', 'Home Page'), (b'INHERIT', 'Inherit the template of the nearest ancestor')]),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='language',
            field=models.CharField(help_text='The language for the admin interface and toolbar', max_length=10, verbose_name='Language', choices=[(b'en', b'en')]),
        ),
    ]
