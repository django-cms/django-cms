# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_pandadocdocumentsenderplugin_message_content'),
    ]

    operations = [
        migrations.CreateModel(
            name='PandadocAuthentication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Can be anything useful to help identify this authentication object amongst others.', max_length=255, verbose_name='Authentication name')),
                ('client_id', models.CharField(max_length=255, verbose_name='Client ID')),
                ('client_secret', models.CharField(max_length=255, verbose_name='Client secret')),
                ('redirect_uri', models.CharField(max_length=255, verbose_name='Redirect URI')),
                ('scope', models.CharField(default=b'read+write', max_length=255, verbose_name='Scope')),
                ('access_token', models.CharField(default=b'', max_length=255, verbose_name='Access token', blank=True)),
                ('refresh_token', models.CharField(default=b'', max_length=255, verbose_name='Refresh token', blank=True)),
                ('token_expiration', models.DateTimeField(null=True, verbose_name='Token expiration', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='pandadocdocumentsenderplugin',
            name='access_token',
        ),
        migrations.RemoveField(
            model_name='pandadocdocumentsenderplugin',
            name='refresh_token',
        ),
        migrations.AlterField(
            model_name='pandadocdocumentsenderplugin',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='project_pandadocdocumentsenderplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.AddField(
            model_name='pandadocdocumentsenderplugin',
            name='authentication',
            field=models.ForeignKey(verbose_name='Authentication', blank=True, to='project.PandadocAuthentication', null=True),
        ),
    ]
