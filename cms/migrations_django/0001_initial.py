# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields
import django.utils.timezone
from django.conf import settings
import cms.models.static_placeholder


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='CMSPlugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.PositiveSmallIntegerField(verbose_name='position', null=True, editable=False, blank=True)),
                ('language', models.CharField(verbose_name='language', max_length=15, editable=False, db_index=True)),
                ('plugin_type', models.CharField(verbose_name='plugin name', max_length=50, editable=False, db_index=True)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation date', editable=False)),
                ('changed_date', models.DateTimeField(auto_now=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AliasPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('plugin', models.ForeignKey(editable=False, to='cms.CMSPlugin', null=True)),
            ],
            options={
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.AddField(
            model_name='cmsplugin',
            name='parent',
            field=models.ForeignKey(blank=True, editable=False, to='cms.CMSPlugin', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='GlobalPagePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('can_change', models.BooleanField(default=True, verbose_name='can edit')),
                ('can_add', models.BooleanField(default=True, verbose_name='can add')),
                ('can_delete', models.BooleanField(default=True, verbose_name='can delete')),
                ('can_change_advanced_settings', models.BooleanField(default=False, verbose_name='can change advanced settings')),
                ('can_publish', models.BooleanField(default=True, verbose_name='can publish')),
                ('can_change_permissions', models.BooleanField(default=False, help_text='on page level', verbose_name='can change permissions')),
                ('can_move_page', models.BooleanField(default=True, verbose_name='can move')),
                ('can_view', models.BooleanField(default=False, help_text='frontend view restriction', verbose_name='view restricted')),
                ('can_recover_page', models.BooleanField(default=True, help_text='can recover any deleted page', verbose_name='can recover pages')),
                ('group', models.ForeignKey(verbose_name='group', blank=True, to='auth.Group', null=True)),
                ('sites', models.ManyToManyField(to='sites.Site', null=True, verbose_name='sites', blank=True)),
                ('user', models.ForeignKey(verbose_name='user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_by', models.CharField(verbose_name='created by', max_length=70, editable=False)),
                ('changed_by', models.CharField(verbose_name='changed by', max_length=70, editable=False)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('changed_date', models.DateTimeField(auto_now=True)),
                ('publication_date', models.DateTimeField(help_text='When the page should go live. Status must be "Published" for page to go live.', null=True, verbose_name='publication date', db_index=True, blank=True)),
                ('publication_end_date', models.DateTimeField(help_text='When to expire the page. Leave empty to never expire.', null=True, verbose_name='publication end date', db_index=True, blank=True)),
                ('in_navigation', models.BooleanField(default=True, db_index=True, verbose_name='in navigation')),
                ('soft_root', models.BooleanField(default=False, help_text='All ancestors will not be displayed in the navigation', db_index=True, verbose_name='soft root')),
                ('reverse_id', models.CharField(max_length=40, blank=True, help_text='A unique identifier that is used with the page_url templatetag for linking to this page', null=True, verbose_name='id', db_index=True)),
                ('navigation_extenders', models.CharField(db_index=True, max_length=80, null=True, verbose_name='attached menu', blank=True)),
                ('template', models.CharField(default='INHERIT', help_text='The template used to render the content.', max_length=100, verbose_name='template', choices=[('col_two.html', 'two columns'), ('col_three.html', 'three columns'), ('nav_playground.html', 'navigation examples'), ('simple.html', 'simple'), ('static.html', 'static placeholders'), ('INHERIT', 'Inherit the template of the nearest ancestor')])),
                ('login_required', models.BooleanField(default=False, verbose_name='login required')),
                ('limit_visibility_in_menu', models.SmallIntegerField(default=None, choices=[(1, 'for logged in users only'), (2, 'for anonymous users only')], blank=True, help_text='limit when this page is visible in the menu', null=True, verbose_name='menu visibility', db_index=True)),
                ('is_home', models.BooleanField(default=False, db_index=True, editable=False)),
                ('application_urls', models.CharField(db_index=True, max_length=200, null=True, verbose_name='application', blank=True)),
                ('application_namespace', models.CharField(max_length=200, null=True, verbose_name='application instance name', blank=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('publisher_is_draft', models.BooleanField(default=True, db_index=True, editable=False)),
                ('languages', models.CharField(max_length=255, null=True, editable=False, blank=True)),
                ('revision_id', models.PositiveIntegerField(default=0, editable=False)),
                ('xframe_options', models.IntegerField(default=0, choices=[(0, 'Inherit from parent page'), (1, 'Deny'), (2, 'Only this website'), (3, 'Allow')])),
                ('parent', models.ForeignKey(blank=True, to='cms.Page', null=True)),
                ('publisher_public', models.OneToOneField(null=True, editable=False, to='cms.Page')),
                ('site', models.ForeignKey(verbose_name='site', to='sites.Site', help_text='The site the page is accessible at.')),
            ],
            options={
                'ordering': ('tree_id', 'lft'),
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'permissions': (('view_page', 'Can view page'), ('publish_page', 'Can publish page')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PagePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('can_change', models.BooleanField(default=True, verbose_name='can edit')),
                ('can_add', models.BooleanField(default=True, verbose_name='can add')),
                ('can_delete', models.BooleanField(default=True, verbose_name='can delete')),
                ('can_change_advanced_settings', models.BooleanField(default=False, verbose_name='can change advanced settings')),
                ('can_publish', models.BooleanField(default=True, verbose_name='can publish')),
                ('can_change_permissions', models.BooleanField(default=False, help_text='on page level', verbose_name='can change permissions')),
                ('can_move_page', models.BooleanField(default=True, verbose_name='can move')),
                ('can_view', models.BooleanField(default=False, help_text='frontend view restriction', verbose_name='view restricted')),
                ('grant_on', models.IntegerField(default=5, verbose_name='Grant on', choices=[(1, 'Current page'), (2, 'Page children (immediate)'), (3, 'Page and children (immediate)'), (4, 'Page descendants'), (5, 'Page and descendants')])),
                ('group', models.ForeignKey(verbose_name='group', blank=True, to='auth.Group', null=True)),
                ('page', models.ForeignKey(verbose_name='page', blank=True, to='cms.Page', null=True)),
                ('user', models.ForeignKey(verbose_name='user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Page permission',
                'verbose_name_plural': 'Page permissions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageUser',
            fields=[
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('user_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User (page)',
                'verbose_name_plural': 'Users (page)',
            },
            bases=('auth.user',),
        ),
        migrations.CreateModel(
            name='PageUserGroup',
            fields=[
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('group_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
            ],
            options={
                'verbose_name': 'User group (page)',
                'verbose_name_plural': 'User groups (page)',
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Placeholder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slot', models.CharField(verbose_name='slot', max_length=50, editable=False, db_index=True)),
                ('default_width', models.PositiveSmallIntegerField(verbose_name='width', null=True, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='page',
            name='placeholders',
            field=models.ManyToManyField(to='cms.Placeholder', editable=False),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('reverse_id', 'site', 'publisher_is_draft'), ('publisher_is_draft', 'application_namespace')]),
        ),
        migrations.AddField(
            model_name='cmsplugin',
            name='placeholder',
            field=models.ForeignKey(editable=False, to='cms.Placeholder', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aliaspluginmodel',
            name='alias_placeholder',
            field=models.ForeignKey(editable=False, to='cms.Placeholder', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PlaceholderReference',
            fields=[
                ('name', models.CharField(max_length=255)),
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('placeholder_ref', cms.models.fields.PlaceholderField(slotname='clipboard', editable=False, to='cms.Placeholder', null=True)),
            ],
            options={
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='StaticPlaceholder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', help_text='Descriptive name to identify this static placeholder. Not displayed to users.', max_length=255, verbose_name='static placeholder name', blank=True)),
                ('code', models.CharField(help_text='To render the static placeholder in templates.', max_length=255, verbose_name='placeholder code', blank=True)),
                ('dirty', models.BooleanField(default=False, editable=False)),
                ('creation_method', models.CharField(default='code', max_length=20, verbose_name='creation_method', blank=True, choices=[('template', 'by template'), ('code', 'by code')])),
                ('draft', cms.models.fields.PlaceholderField(slotname=cms.models.static_placeholder.static_slotname, editable=False, to='cms.Placeholder', null=True, verbose_name='placeholder content')),
                ('public', cms.models.fields.PlaceholderField(slotname=cms.models.static_placeholder.static_slotname, editable=False, to='cms.Placeholder', null=True)),
                ('site', models.ForeignKey(blank=True, to='sites.Site', null=True)),
            ],
            options={
                'verbose_name': 'static placeholder',
                'verbose_name_plural': 'static placeholders',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='staticplaceholder',
            unique_together=set([('code', 'site')]),
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(max_length=15, verbose_name='language', db_index=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('page_title', models.CharField(help_text='overwrite the title (html title tag)', max_length=255, null=True, verbose_name='title', blank=True)),
                ('menu_title', models.CharField(help_text='overwrite the title in the menu', max_length=255, null=True, verbose_name='title', blank=True)),
                ('meta_description', models.TextField(help_text='The text displayed in search engines.', max_length=155, null=True, verbose_name='description', blank=True)),
                ('slug', models.SlugField(max_length=255, verbose_name='slug')),
                ('path', models.CharField(max_length=255, verbose_name='Path', db_index=True)),
                ('has_url_overwrite', models.BooleanField(default=False, verbose_name='has URL overwrite', db_index=True, editable=False)),
                ('redirect', models.CharField(max_length=255, null=True, verbose_name='redirect', blank=True)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation date', editable=False)),
                ('published', models.BooleanField(default=False, verbose_name='is published')),
                ('publisher_is_draft', models.BooleanField(default=True, db_index=True, editable=False)),
                ('publisher_state', models.SmallIntegerField(default=0, editable=False, db_index=True)),
                ('page', models.ForeignKey(verbose_name='page', to='cms.Page')),
                ('publisher_public', models.OneToOneField(null=True, editable=False, to='cms.Title')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='title',
            unique_together=set([('language', 'page')]),
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text='The language for the admin interface and toolbar', max_length=10, verbose_name='Language', choices=[('en', 'English'), ('fr', 'French'), ('de', 'German'), ('pt-br', 'Brazilian Portuguese'), ('nl', 'Dutch'), ('es-mx', 'Espa\xf1ol')])),
                ('clipboard', models.ForeignKey(blank=True, editable=False, to='cms.Placeholder', null=True)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
                'verbose_name': 'user setting',
                'verbose_name_plural': 'user settings',
            },
            bases=(models.Model,),
        ),
    ]
