# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cms.models.fields
from django.conf import settings
import django.utils.timezone
import cms.models.static_placeholder


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CMSPlugin',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('position', models.PositiveSmallIntegerField(editable=False, verbose_name='position', blank=True, null=True)),
                ('language', models.CharField(editable=False, verbose_name='language', db_index=True, max_length=15)),
                ('plugin_type', models.CharField(editable=False, verbose_name='plugin name', db_index=True, max_length=50)),
                ('creation_date', models.DateTimeField(editable=False, verbose_name='creation date', default=django.utils.timezone.now)),
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
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
                ('plugin', models.ForeignKey(related_name='alias_reference', editable=False, to='cms.CMSPlugin', null=True)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('can_change', models.BooleanField(verbose_name='can edit', default=True)),
                ('can_add', models.BooleanField(verbose_name='can add', default=True)),
                ('can_delete', models.BooleanField(verbose_name='can delete', default=True)),
                ('can_change_advanced_settings', models.BooleanField(verbose_name='can change advanced settings', default=False)),
                ('can_publish', models.BooleanField(verbose_name='can publish', default=True)),
                ('can_change_permissions', models.BooleanField(help_text='on page level', default=False, verbose_name='can change permissions')),
                ('can_move_page', models.BooleanField(verbose_name='can move', default=True)),
                ('can_view', models.BooleanField(help_text='frontend view restriction', default=False, verbose_name='view restricted')),
                ('can_recover_page', models.BooleanField(help_text='can recover any deleted page', default=True, verbose_name='can recover pages')),
                ('group', models.ForeignKey(blank=True, verbose_name='group', to='auth.Group', null=True)),
                ('sites', models.ManyToManyField(help_text='If none selected, user haves granted permissions to all sites.', blank=True, to='sites.Site', null=True, verbose_name='sites')),
                ('user', models.ForeignKey(blank=True, verbose_name='user', to=settings.AUTH_USER_MODEL, null=True)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_by', models.CharField(editable=False, verbose_name='created by', max_length=70)),
                ('changed_by', models.CharField(editable=False, verbose_name='changed by', max_length=70)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('changed_date', models.DateTimeField(auto_now=True)),
                ('publication_date', models.DateTimeField(help_text='When the page should go live. Status must be "Published" for page to go live.', blank=True, db_index=True, null=True, verbose_name='publication date')),
                ('publication_end_date', models.DateTimeField(help_text='When to expire the page. Leave empty to never expire.', blank=True, db_index=True, null=True, verbose_name='publication end date')),
                ('in_navigation', models.BooleanField(verbose_name='in navigation', db_index=True, default=True)),
                ('soft_root', models.BooleanField(help_text='All ancestors will not be displayed in the navigation', db_index=True, default=False, verbose_name='soft root')),
                ('reverse_id', models.CharField(help_text='A unique identifier that is used with the page_url templatetag for linking to this page', blank=True, max_length=40, verbose_name='id', db_index=True, null=True)),
                ('navigation_extenders', models.CharField(verbose_name='attached menu', blank=True, null=True, max_length=80, db_index=True)),
                ('template', models.CharField(help_text='The template used to render the content.', choices=[('col_two.html', 'two columns'), ('col_three.html', 'three columns'), ('nav_playground.html', 'navigation examples'), ('simple.html', 'simple'), ('static.html', 'static placeholders'), ('INHERIT', 'Inherit the template of the nearest ancestor')], default='INHERIT', max_length=100, verbose_name='template')),
                ('login_required', models.BooleanField(verbose_name='login required', default=False)),
                ('limit_visibility_in_menu', models.SmallIntegerField(help_text='limit when this page is visible in the menu', blank=True, choices=[(1, 'for logged in users only'), (2, 'for anonymous users only')], verbose_name='menu visibility', db_index=True, default=None, null=True)),
                ('is_home', models.BooleanField(editable=False, db_index=True, default=False)),
                ('application_urls', models.CharField(verbose_name='application', blank=True, null=True, max_length=200, db_index=True)),
                ('application_namespace', models.CharField(verbose_name='application instance name', blank=True, null=True, max_length=200)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('publisher_is_draft', models.BooleanField(editable=False, db_index=True, default=True)),
                ('languages', models.CharField(editable=False, blank=True, null=True, max_length=255)),
                ('revision_id', models.PositiveIntegerField(editable=False, default=0)),
                ('xframe_options', models.IntegerField(choices=[(0, 'Inherit from parent page'), (1, 'Deny'), (2, 'Only this website'), (3, 'Allow')], default=0)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='cms.Page', null=True)),
                ('publisher_public', models.OneToOneField(related_name='publisher_draft', editable=False, to='cms.Page', null=True)),
                ('site', models.ForeignKey(help_text='The site the page is accessible at.', related_name='djangocms_pages', verbose_name='site', to='sites.Site')),
            ],
            options={
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'ordering': ('tree_id', 'lft'),
                'permissions': (('view_page', 'Can view page'), ('publish_page', 'Can publish page'), ('edit_static_placeholder', 'Can edit static placeholders')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PagePermission',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('can_change', models.BooleanField(verbose_name='can edit', default=True)),
                ('can_add', models.BooleanField(verbose_name='can add', default=True)),
                ('can_delete', models.BooleanField(verbose_name='can delete', default=True)),
                ('can_change_advanced_settings', models.BooleanField(verbose_name='can change advanced settings', default=False)),
                ('can_publish', models.BooleanField(verbose_name='can publish', default=True)),
                ('can_change_permissions', models.BooleanField(help_text='on page level', default=False, verbose_name='can change permissions')),
                ('can_move_page', models.BooleanField(verbose_name='can move', default=True)),
                ('can_view', models.BooleanField(help_text='frontend view restriction', default=False, verbose_name='view restricted')),
                ('grant_on', models.IntegerField(verbose_name='Grant on', default=5, choices=[(1, 'Current page'), (2, 'Page children (immediate)'), (3, 'Page and children (immediate)'), (4, 'Page descendants'), (5, 'Page and descendants')])),
                ('group', models.ForeignKey(blank=True, verbose_name='group', to='auth.Group', null=True)),
                ('page', models.ForeignKey(blank=True, verbose_name='page', to='cms.Page', null=True)),
                ('user', models.ForeignKey(blank=True, verbose_name='user', to=settings.AUTH_USER_MODEL, null=True)),
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
                ('user_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to=settings.AUTH_USER_MODEL, primary_key=True)),
                ('created_by', models.ForeignKey(related_name='created_users', to=settings.AUTH_USER_MODEL)),
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
                ('group_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='auth.Group', primary_key=True)),
                ('created_by', models.ForeignKey(related_name='created_usergroups', to=settings.AUTH_USER_MODEL)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('slot', models.CharField(editable=False, verbose_name='slot', db_index=True, max_length=50)),
                ('default_width', models.PositiveSmallIntegerField(editable=False, verbose_name='width', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='page',
            name='placeholders',
            field=models.ManyToManyField(editable=False, to='cms.Placeholder'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('publisher_is_draft', 'application_namespace'), ('reverse_id', 'site', 'publisher_is_draft')]),
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
            field=models.ForeignKey(related_name='alias_placeholder', editable=False, to='cms.Placeholder', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PlaceholderReference',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='cms.CMSPlugin', primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('placeholder_ref', cms.models.fields.PlaceholderField(editable=False, to='cms.Placeholder', null=True, slotname='clipboard')),
            ],
            options={
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='StaticPlaceholder',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Descriptive name to identify this static placeholder. Not displayed to users.', blank=True, default='', max_length=255, verbose_name='static placeholder name')),
                ('code', models.CharField(help_text='To render the static placeholder in templates.', blank=True, max_length=255, verbose_name='placeholder code')),
                ('dirty', models.BooleanField(editable=False, default=False)),
                ('creation_method', models.CharField(verbose_name='creation_method', blank=True, default='code', max_length=20, choices=[('template', 'by template'), ('code', 'by code')])),
                ('draft', cms.models.fields.PlaceholderField(related_name='static_draft', editable=False, verbose_name='placeholder content', to='cms.Placeholder', null=True, slotname=cms.models.static_placeholder.static_slotname)),
                ('public', cms.models.fields.PlaceholderField(related_name='static_public', editable=False, to='cms.Placeholder', null=True, slotname=cms.models.static_placeholder.static_slotname)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('language', models.CharField(verbose_name='language', db_index=True, max_length=15)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('page_title', models.CharField(help_text='overwrite the title (html title tag)', blank=True, null=True, max_length=255, verbose_name='title')),
                ('menu_title', models.CharField(help_text='overwrite the title in the menu', blank=True, null=True, max_length=255, verbose_name='title')),
                ('meta_description', models.TextField(help_text='The text displayed in search engines.', blank=True, null=True, max_length=155, verbose_name='description')),
                ('slug', models.SlugField(verbose_name='slug', max_length=255)),
                ('path', models.CharField(verbose_name='Path', db_index=True, max_length=255)),
                ('has_url_overwrite', models.BooleanField(editable=False, verbose_name='has URL overwrite', db_index=True, default=False)),
                ('redirect', models.CharField(verbose_name='redirect', blank=True, null=True, max_length=255)),
                ('creation_date', models.DateTimeField(editable=False, verbose_name='creation date', default=django.utils.timezone.now)),
                ('published', models.BooleanField(verbose_name='is published', default=False)),
                ('publisher_is_draft', models.BooleanField(editable=False, db_index=True, default=True)),
                ('publisher_state', models.SmallIntegerField(editable=False, db_index=True, default=0)),
                ('page', models.ForeignKey(related_name='title_set', verbose_name='page', to='cms.Page')),
                ('publisher_public', models.OneToOneField(related_name='publisher_draft', editable=False, to='cms.Title', null=True)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text='The language for the admin interface and toolbar', choices=[('en', 'English'), ('fr', 'French'), ('de', 'German'), ('pt-br', 'Brazilian Portuguese'), ('nl', 'Dutch'), ('es-mx', 'Español')], max_length=10, verbose_name='Language')),
                ('clipboard', models.ForeignKey(blank=True, editable=False, to='cms.Placeholder', null=True)),
                ('user', models.ForeignKey(related_name='djangocms_usersettings', editable=False, unique=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'user setting',
                'verbose_name_plural': 'user settings',
            },
            bases=(models.Model,),
        ),
    ]
