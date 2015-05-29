# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangocms_text_ckeditor.fields
import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_auto_20150419_1006'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=40)),
                ('is_active', models.BooleanField(default=True, help_text=b'published on the web site')),
                ('email', models.EmailField(max_length=75)),
                ('is_alive', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100)),
                ('is_active', models.BooleanField(default=True, help_text=b'published on the web site')),
                ('publication_date', models.DateField()),
                ('still_published', models.BooleanField(default=True)),
                ('public_domain', models.BooleanField(default=False)),
                ('language', models.CharField(default=b'eng', max_length=3, choices=[(b'eng', 'Anglais'), (b'fre', 'Fran\xe7ais'), (b'srj', 'Sindarin')])),
                ('summary', djangocms_text_ckeditor.fields.HTMLField()),
                ('nb_pages', models.PositiveSmallIntegerField()),
                ('authors', models.ManyToManyField(to='custommodelapp.Author')),
                ('description', cms.models.fields.PlaceholderField(slotname=b'book_description', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
                'ordering': ['-publication_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DVD',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100)),
                ('is_active', models.BooleanField(default=True, help_text=b'published on the web site')),
                ('publication_date', models.DateField()),
                ('still_published', models.BooleanField(default=True)),
                ('public_domain', models.BooleanField(default=False)),
                ('language', models.CharField(default=b'eng', max_length=3, choices=[(b'eng', 'Anglais'), (b'fre', 'Fran\xe7ais'), (b'srj', 'Sindarin')])),
                ('summary', djangocms_text_ckeditor.fields.HTMLField()),
                ('duration', models.PositiveSmallIntegerField(help_text=b'in minutes')),
                ('authors', models.ManyToManyField(to='custommodelapp.Author')),
                ('description', cms.models.fields.PlaceholderField(slotname=b'book_description', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
                'ordering': ['-publication_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('slug', models.SlugField(max_length=30)),
                ('is_active', models.BooleanField(default=True, help_text=b'published on the web site')),
                ('address', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=60)),
                ('zip_code', models.CharField(max_length=10)),
                ('country', models.CharField(max_length=50)),
                ('website', models.URLField()),
                ('presentation', djangocms_text_ckeditor.fields.HTMLField()),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='dvd',
            name='publisher',
            field=models.ForeignKey(to='custommodelapp.Publisher'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='publisher',
            field=models.ForeignKey(to='custommodelapp.Publisher'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PublicBookProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Book in public domain',
                'proxy': True,
                'verbose_name_plural': 'Books in public domain',
            },
            bases=('custommodelapp.book',),
        ),
    ]
