# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserObjectPermission',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('object_pk', models.CharField(verbose_name='object ID', max_length=255)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('permission', models.ForeignKey(to='auth.Permission')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userobjectpermission',
            unique_together=set([('user', 'permission', 'object_pk')]),
        ),
    ]
