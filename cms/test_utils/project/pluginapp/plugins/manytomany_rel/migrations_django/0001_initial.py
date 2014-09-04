# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('title', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ArticlePluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(primary_key=True, to='cms.CMSPlugin', auto_created=True, parent_link=True, serialize=False)),
                ('title', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='articlepluginmodel',
            name='sections',
            field=models.ManyToManyField(to='manytomany_rel.Section'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='section',
            field=models.ForeignKey(to='manytomany_rel.Section'),
            preserve_default=True,
        ),
    ]
