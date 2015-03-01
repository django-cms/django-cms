# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


try:
    from django.contrib.auth import get_user_model
except ImportError: # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

user_orm_label = '%s.%s' % (User._meta.app_label, User._meta.object_name)
user_model_label = '%s.%s' % (User._meta.app_label, User._meta.model_name)
user_ptr_name = '%s_ptr' % User._meta.object_name.lower()

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Placeholder'
        db.create_table('cms_placeholder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slot', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('default_width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
        ))
        db.send_create_signal('cms', ['Placeholder'])

        # Adding model 'CMSPlugin'
        db.create_table('cms_cmsplugin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('placeholder', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.CMSPlugin'], null=True, blank=True)),
            ('position', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('plugin_type', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('changed_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('cms', ['CMSPlugin'])

        # Adding model 'Page'
        db.create_table('cms_page', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_by', self.gf('django.db.models.fields.CharField')(max_length=70)),
            ('changed_by', self.gf('django.db.models.fields.CharField')(max_length=70)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['cms.Page'])),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('changed_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('publication_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('publication_end_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('in_navigation', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('soft_root', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('reverse_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=40, null=True, blank=True)),
            ('navigation_extenders', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=80, null=True, blank=True)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('moderator_state', self.gf('django.db.models.fields.SmallIntegerField')(default=1, blank=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('login_required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('limit_visibility_in_menu', self.gf('django.db.models.fields.SmallIntegerField')(default=None, null=True, db_index=True, blank=True)),
            ('publisher_is_draft', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('publisher_public', self.gf('django.db.models.fields.related.OneToOneField')(related_name='publisher_draft', unique=True, null=True, to=orm['cms.Page'])),
            ('publisher_state', self.gf('django.db.models.fields.SmallIntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('cms', ['Page'])

        # Adding M2M table for field placeholders on 'Page'
        db.create_table('cms_page_placeholders', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm['cms.page'], null=False)),
            ('placeholder', models.ForeignKey(orm['cms.placeholder'], null=False))
        ))
        db.create_unique('cms_page_placeholders', ['page_id', 'placeholder_id'])

        # Adding model 'PageModerator'
        db.create_table('cms_pagemoderator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Page'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[user_orm_label])),
            ('moderate_page', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('moderate_children', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('moderate_descendants', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cms', ['PageModerator'])

        # Adding model 'PageModeratorState'
        db.create_table('cms_pagemoderatorstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Page'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[user_orm_label], null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(default='', max_length=1000, blank=True)),
        ))
        db.send_create_signal('cms', ['PageModeratorState'])

        # Adding model 'GlobalPagePermission'
        db.create_table('cms_globalpagepermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[user_orm_label], null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True, blank=True)),
            ('can_change', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_add', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_delete', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_change_advanced_settings', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_publish', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_change_permissions', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_move_page', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_moderate', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_view', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_recover_page', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('cms', ['GlobalPagePermission'])

        # Adding M2M table for field sites on 'GlobalPagePermission'
        db.create_table('cms_globalpagepermission_sites', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('globalpagepermission', models.ForeignKey(orm['cms.globalpagepermission'], null=False)),
            ('site', models.ForeignKey(orm['sites.site'], null=False))
        ))
        db.create_unique('cms_globalpagepermission_sites', ['globalpagepermission_id', 'site_id'])

        # Adding model 'PagePermission'
        db.create_table('cms_pagepermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[user_orm_label], null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True, blank=True)),
            ('can_change', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_add', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_delete', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_change_advanced_settings', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_publish', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_change_permissions', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_move_page', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_moderate', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_view', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('grant_on', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Page'], null=True, blank=True)),
        ))
        db.send_create_signal('cms', ['PagePermission'])

        # Adding model 'PageUser'
        db.create_table('cms_pageuser', (
            (user_ptr_name, self.gf('django.db.models.fields.related.OneToOneField')(to=orm[user_orm_label], unique=True, primary_key=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_users', to=orm[user_orm_label])),
        ))
        db.send_create_signal('cms', ['PageUser'])

        # Adding model 'PageUserGroup'
        db.create_table('cms_pageusergroup', (
            ('group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_usergroups', to=orm[user_orm_label])),
        ))
        db.send_create_signal('cms', ['PageUserGroup'])

        # Adding model 'Title'
        db.create_table('cms_title', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('menu_title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('has_url_overwrite', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('application_urls', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=200, null=True, blank=True)),
            ('redirect', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('meta_description', self.gf('django.db.models.fields.TextField')(max_length=255, null=True, blank=True)),
            ('meta_keywords', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('page_title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='title_set', to=orm['cms.Page'])),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('cms', ['Title'])

        # Adding unique constraint on 'Title', fields ['language', 'page']
        db.create_unique('cms_title', ['language', 'page_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Title', fields ['language', 'page']
        db.delete_unique('cms_title', ['language', 'page_id'])

        # Deleting model 'Placeholder'
        db.delete_table('cms_placeholder')

        # Deleting model 'CMSPlugin'
        db.delete_table('cms_cmsplugin')

        # Deleting model 'Page'
        db.delete_table('cms_page')

        # Removing M2M table for field placeholders on 'Page'
        db.delete_table('cms_page_placeholders')

        # Deleting model 'PageModerator'
        db.delete_table('cms_pagemoderator')

        # Deleting model 'PageModeratorState'
        db.delete_table('cms_pagemoderatorstate')

        # Deleting model 'GlobalPagePermission'
        db.delete_table('cms_globalpagepermission')

        # Removing M2M table for field sites on 'GlobalPagePermission'
        db.delete_table('cms_globalpagepermission_sites')

        # Deleting model 'PagePermission'
        db.delete_table('cms_pagepermission')

        # Deleting model 'PageUser'
        db.delete_table('cms_pageuser')

        # Deleting model 'PageUserGroup'
        db.delete_table('cms_pageusergroup')

        # Deleting model 'Title'
        db.delete_table('cms_title')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        user_model_label: {
            'Meta': {'object_name': User.__name__, 'db_table': "'%s'" % User._meta.db_table},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cms.cmsplugin': {
            'Meta': {'object_name': 'CMSPlugin'},
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.globalpagepermission': {
            'Meta': {'object_name': 'GlobalPagePermission'},
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_change_advanced_settings': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_recover_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_view': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_orm_label, 'null': 'True', 'blank': 'True'})
        },
        'cms.page': {
            'Meta': {'ordering': "('site', 'tree_id', 'lft')", 'object_name': 'Page'},
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'limit_visibility_in_menu': ('django.db.models.fields.SmallIntegerField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['cms.Page']"}),
            'placeholders': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cms.Placeholder']", 'symmetrical': 'False'}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagemoderator': {
            'Meta': {'object_name': 'PageModerator'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderate_children': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderate_descendants': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderate_page': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_orm_label})
        },
        'cms.pagemoderatorstate': {
            'Meta': {'ordering': "('page', 'action', '-created')", 'object_name': 'PageModeratorState'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_orm_label, 'null': 'True'})
        },
        'cms.pagepermission': {
            'Meta': {'object_name': 'PagePermission'},
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_change_advanced_settings': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_view': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'grant_on': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_orm_label, 'null': 'True', 'blank': 'True'})
        },
        'cms.pageuser': {
            'Meta': {'object_name': 'PageUser', '_ormbases': [user_orm_label]},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_users'", 'to': "orm['%s']" % user_orm_label}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['%s']" % user_orm_label, 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.pageusergroup': {
            'Meta': {'object_name': 'PageUserGroup', '_ormbases': ['auth.Group']},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_usergroups'", 'to': "orm['%s']" % user_orm_label}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'cms.title': {
            'Meta': {'unique_together': "(('language', 'page'),)", 'object_name': 'Title'},
            'application_urls': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'has_url_overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'menu_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'title_set'", 'to': "orm['cms.Page']"}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'redirect': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['cms']
