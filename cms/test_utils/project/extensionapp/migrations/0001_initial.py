# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cms', '0002_auto_20140816_1918'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyPageExtension',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('extra', models.CharField(max_length=255, default='', blank=True)),
                ('extended_object', models.OneToOneField(to='cms.Page', editable=False)),
                ('favorite_users', models.ManyToManyField(null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('public_extension', models.OneToOneField(null=True, to='extensionapp.MyPageExtension', related_name='draft_extension', editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MyTitleExtension',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('extra_title', models.CharField(max_length=255, default='', blank=True)),
                ('extended_object', models.OneToOneField(to='cms.Title', editable=False)),
                ('public_extension', models.OneToOneField(null=True, to='extensionapp.MyTitleExtension', related_name='draft_extension', editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
