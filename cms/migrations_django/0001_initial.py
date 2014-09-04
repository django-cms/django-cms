# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CMSPlugin',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('position', models.PositiveSmallIntegerField(null=True, editable=False, blank=True, verbose_name='position')),
                ('language', models.CharField(db_index=True, max_length=15, verbose_name='language', editable=False)),
                ('plugin_type', models.CharField(db_index=True, max_length=50, verbose_name='plugin name', editable=False)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation date', editable=False)),
                ('changed_date', models.DateTimeField(auto_now=True)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AliasPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(primary_key=True, to='cms.CMSPlugin', auto_created=True, parent_link=True, serialize=False)),
                ('plugin', models.ForeignKey(null=True, to='cms.CMSPlugin', related_name='alias_reference', editable=False)),
            ],
            options={
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.AddField(
            model_name='cmsplugin',
            name='parent',
            field=models.ForeignKey(null=True, to='cms.CMSPlugin', blank=True, editable=False),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='GlobalPagePermission',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('can_change', models.BooleanField(default=True, verbose_name='can edit')),
                ('can_add', models.BooleanField(default=True, verbose_name='can add')),
                ('can_delete', models.BooleanField(default=True, verbose_name='can delete')),
                ('can_change_advanced_settings', models.BooleanField(default=False, verbose_name='can change advanced settings')),
                ('can_publish', models.BooleanField(default=True, verbose_name='can publish')),
                ('can_change_permissions', models.BooleanField(default=False, help_text='on page level', verbose_name='can change permissions')),
                ('can_move_page', models.BooleanField(default=True, verbose_name='can move')),
                ('can_view', models.BooleanField(default=False, help_text='frontend view restriction', verbose_name='view restricted')),
                ('can_recover_page', models.BooleanField(default=True, help_text='can recover any deleted page', verbose_name='can recover pages')),
                ('group', models.ForeignKey(null=True, to='auth.Group', verbose_name='group', blank=True)),
                ('sites', models.ManyToManyField(null=True, help_text='If none selected, user haves granted permissions to all sites.', blank=True, to='sites.Site', verbose_name='sites')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='user', blank=True)),
            ],
            options={
                'verbose_name': 'Page global permission',
                'verbose_name_plural': 'Pages global permissions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_by', models.CharField(max_length=70, verbose_name='created by', editable=False)),
                ('changed_by', models.CharField(max_length=70, verbose_name='changed by', editable=False)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('changed_date', models.DateTimeField(auto_now=True)),
                ('publication_date', models.DateTimeField(db_index=True, null=True, help_text='When the page should go live. Status must be "Published" for page to go live.', blank=True, verbose_name='publication date')),
                ('publication_end_date', models.DateTimeField(db_index=True, null=True, help_text='When to expire the page. Leave empty to never expire.', blank=True, verbose_name='publication end date')),
                ('in_navigation', models.BooleanField(db_index=True, default=True, verbose_name='in navigation')),
                ('soft_root', models.BooleanField(db_index=True, default=False, help_text='All ancestors will not be displayed in the navigation', verbose_name='soft root')),
                ('reverse_id', models.CharField(db_index=True, max_length=40, verbose_name='id', null=True, help_text='A unique identifier that is used with the page_url templatetag for linking to this page', blank=True)),
                ('navigation_extenders', models.CharField(db_index=True, max_length=80, blank=True, verbose_name='attached menu', null=True)),
                ('template', models.CharField(max_length=100, default='INHERIT', help_text='The template used to render the content.', verbose_name='template', choices=[('col_two.html', 'two columns'), ('col_three.html', 'three columns'), ('nav_playground.html', 'navigation examples'), ('simple.html', 'simple'), ('static.html', 'static placeholders'), ('INHERIT', 'Inherit the template of the nearest ancestor')])),
                ('login_required', models.BooleanField(default=False, verbose_name='login required')),
                ('limit_visibility_in_menu', models.SmallIntegerField(db_index=True, default=None, verbose_name='menu visibility', null=True, choices=[(1, 'for logged in users only'), (2, 'for anonymous users only')], help_text='limit when this page is visible in the menu', blank=True)),
                ('is_home', models.BooleanField(db_index=True, default=False, editable=False)),
                ('application_urls', models.CharField(db_index=True, max_length=200, blank=True, verbose_name='application', null=True)),
                ('application_namespace', models.CharField(max_length=200, null=True, blank=True, verbose_name='application instance name')),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('publisher_is_draft', models.BooleanField(db_index=True, default=True, editable=False)),
                ('languages', models.CharField(max_length=255, null=True, blank=True, editable=False)),
                ('revision_id', models.PositiveIntegerField(default=0, editable=False)),
                ('xframe_options', models.IntegerField(default=0, choices=[(0, 'Inherit from parent page'), (1, 'Deny'), (2, 'Only this website'), (3, 'Allow')])),
                ('parent', models.ForeignKey(null=True, to='cms.Page', related_name='children', blank=True)),
                ('publisher_public', models.OneToOneField(null=True, to='cms.Page', related_name='publisher_draft', editable=False)),
                ('site', models.ForeignKey(to='sites.Site', verbose_name='site', related_name='djangocms_pages', help_text='The site the page is accessible at.')),
            ],
            options={
                'ordering': ('tree_id', 'lft'),
                'permissions': (('view_page', 'Can view page'), ('publish_page', 'Can publish page'), ('edit_static_placeholder', 'Can edit static placeholders')),
                'verbose_name_plural': 'pages',
                'verbose_name': 'page',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PagePermission',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('can_change', models.BooleanField(default=True, verbose_name='can edit')),
                ('can_add', models.BooleanField(default=True, verbose_name='can add')),
                ('can_delete', models.BooleanField(default=True, verbose_name='can delete')),
                ('can_change_advanced_settings', models.BooleanField(default=False, verbose_name='can change advanced settings')),
                ('can_publish', models.BooleanField(default=True, verbose_name='can publish')),
                ('can_change_permissions', models.BooleanField(default=False, help_text='on page level', verbose_name='can change permissions')),
                ('can_move_page', models.BooleanField(default=True, verbose_name='can move')),
                ('can_view', models.BooleanField(default=False, help_text='frontend view restriction', verbose_name='view restricted')),
                ('grant_on', models.IntegerField(default=5, verbose_name='Grant on', choices=[(1, 'Current page'), (2, 'Page children (immediate)'), (3, 'Page and children (immediate)'), (4, 'Page descendants'), (5, 'Page and descendants')])),
                ('group', models.ForeignKey(null=True, to='auth.Group', verbose_name='group', blank=True)),
                ('page', models.ForeignKey(null=True, to='cms.Page', verbose_name='page', blank=True)),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='user', blank=True)),
            ],
            options={
                'verbose_name': 'Page permission',
                'verbose_name_plural': 'Page permissions',
            },
            bases=(models.Model,),
        ),
    ]
