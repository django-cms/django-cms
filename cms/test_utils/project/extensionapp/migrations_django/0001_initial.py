# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MyPageExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra', models.CharField(default=b'', max_length=255, blank=True)),
                ('extended_object', models.OneToOneField(editable=False, to='cms.Page')),
                ('favorite_users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('public_extension', models.OneToOneField(null=True, editable=False, to='extensionapp.MyPageExtension')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MyTitleExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_title', models.CharField(default=b'', max_length=255, blank=True)),
                ('extended_object', models.OneToOneField(editable=False, to='cms.Title')),
                ('public_extension', models.OneToOneField(null=True, editable=False, to='extensionapp.MyTitleExtension')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
