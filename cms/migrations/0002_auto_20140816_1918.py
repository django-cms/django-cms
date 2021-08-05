from __future__ import unicode_literals

import cms.models.static_placeholder
import cms.models.fields
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, migrations
import django.utils.timezone

User = get_user_model()

user_model_label = '%s.%s' % (User._meta.app_label, User._meta.model_name)
user_ptr_name = '%s_ptr' % User._meta.object_name.lower()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageUser',
            fields=[
                (user_ptr_name, models.OneToOneField(primary_key=True, to=settings.AUTH_USER_MODEL, auto_created=True, parent_link=True, serialize=False, on_delete=models.CASCADE)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='created_users', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'User (page)',
                'verbose_name_plural': 'Users (page)',
            },
            bases=(user_model_label,),
        ),
        migrations.CreateModel(
            name='PageUserGroup',
            fields=[
                ('group_ptr', models.OneToOneField(primary_key=True, to='auth.Group', auto_created=True, parent_link=True, serialize=False, on_delete=models.CASCADE)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='created_usergroups', on_delete=models.CASCADE)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('slot', models.CharField(db_index=True, max_length=50, verbose_name='slot', editable=False)),
                ('default_width', models.PositiveSmallIntegerField(null=True, verbose_name='width', editable=False)),
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
            unique_together=set([('publisher_is_draft', 'application_namespace'), ('reverse_id', 'site', 'publisher_is_draft')]),
        ),
        migrations.AddField(
            model_name='cmsplugin',
            name='placeholder',
            field=models.ForeignKey(null=True, to='cms.Placeholder', editable=False, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aliaspluginmodel',
            name='alias_placeholder',
            field=models.ForeignKey(null=True, to='cms.Placeholder', related_name='alias_placeholder', editable=False, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PlaceholderReference',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(primary_key=True, to='cms.CMSPlugin', auto_created=True, parent_link=True, serialize=False, on_delete=models.CASCADE)),
                ('name', models.CharField(max_length=255)),
                ('placeholder_ref', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname='clipboard', editable=False)),
            ],
            options={
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='StaticPlaceholder',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=255, default='', help_text='Descriptive name to identify this static placeholder. Not displayed to users.', blank=True, verbose_name='static placeholder name')),
                ('code', models.CharField(max_length=255, verbose_name='placeholder code', help_text='To render the static placeholder in templates.', blank=True)),
                ('dirty', models.BooleanField(default=False, editable=False)),
                ('creation_method', models.CharField(max_length=20, default='code', blank=True, verbose_name='creation_method', choices=cms.models.static_placeholder.StaticPlaceholder.CREATION_METHODS)),
                ('draft', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', verbose_name='placeholder content', related_name='static_draft', slotname=cms.models.static_placeholder.static_slotname, editable=False)),
                ('public', cms.models.fields.PlaceholderField(null=True, to='cms.Placeholder', slotname=cms.models.static_placeholder.static_slotname, related_name='static_public', editable=False)),
                ('site', models.ForeignKey(null=True, to='sites.Site', blank=True, on_delete=models.CASCADE)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language', models.CharField(db_index=True, max_length=15, verbose_name='language')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('page_title', models.CharField(max_length=255, null=True, help_text='overwrite the title (html title tag)', blank=True, verbose_name='title')),
                ('menu_title', models.CharField(max_length=255, null=True, help_text='overwrite the title in the menu', blank=True, verbose_name='title')),
                ('meta_description', models.TextField(max_length=155, null=True, help_text='The text displayed in search engines.', blank=True, verbose_name='description')),
                ('slug', models.SlugField(max_length=255, verbose_name='slug')),
                ('path', models.CharField(db_index=True, max_length=255, verbose_name='Path')),
                ('has_url_overwrite', models.BooleanField(db_index=True, default=False, editable=False, verbose_name='has url overwrite')),
                ('redirect', models.CharField(max_length=255, null=True, blank=True, verbose_name='redirect')),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation date', editable=False)),
                ('published', models.BooleanField(default=False, verbose_name='is published')),
                ('publisher_is_draft', models.BooleanField(db_index=True, default=True, editable=False)),
                ('publisher_state', models.SmallIntegerField(db_index=True, default=0, editable=False)),
                ('page', models.ForeignKey(to='cms.Page', verbose_name='page', related_name='title_set', on_delete=models.CASCADE)),
                ('publisher_public', models.OneToOneField(null=True, to='cms.Title', related_name='publisher_draft', editable=False, on_delete=models.CASCADE)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language', models.CharField(max_length=10, choices=settings.LANGUAGES, help_text='The language for the admin interface and toolbar', verbose_name='Language')),
                ('clipboard', models.ForeignKey(null=True, to='cms.Placeholder', blank=True, editable=False, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True, related_name='djangocms_usersettings', editable=False, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'user setting',
                'verbose_name_plural': 'user settings',
            },
            bases=(models.Model,),
        ),
    ]
