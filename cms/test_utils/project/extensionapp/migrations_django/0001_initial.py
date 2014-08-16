# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MyPageExtension',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('extra', models.CharField(blank=True, default='', max_length=255)),
                ('extended_object', models.OneToOneField(editable=False, to='cms.Page')),
                ('favorite_users', models.ManyToManyField(blank=True, null=True, to=settings.AUTH_USER_MODEL)),
                ('public_extension', models.OneToOneField(related_name='draft_extension', editable=False, to='extensionapp.MyPageExtension', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MyTitleExtension',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('extra_title', models.CharField(blank=True, default='', max_length=255)),
                ('extended_object', models.OneToOneField(editable=False, to='cms.Title')),
                ('public_extension', models.OneToOneField(related_name='draft_extension', editable=False, to='extensionapp.MyTitleExtension', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
