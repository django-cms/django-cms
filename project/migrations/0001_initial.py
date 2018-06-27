# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0013_urlconfrevision'),
    ]

    operations = [
        migrations.CreateModel(
            name='PandadocDocumentSenderPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('document_name', models.CharField(max_length=255, verbose_name='Pandadoc Document Name')),
                ('template_uuid', models.CharField(help_text='You can copy it from a template url (https://app.pandadoc.com/a/#/templates/{UUID}/content).', max_length=255, verbose_name='Pandadoc Template UUID')),
                ('role', models.CharField(default=b'', help_text='If passed, a person will be assigned all fields which match his or her corresponding role. If not passed, a person will receive a read-only link to view the document.', max_length=255, verbose_name='Role for invited person', blank=True)),
                ('access_token', models.CharField(max_length=255, verbose_name='PandaDoc access token')),
                ('refresh_token', models.CharField(max_length=255, verbose_name='PandaDoc refresh token')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
