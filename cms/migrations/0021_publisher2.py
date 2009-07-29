
from south.db import db
from django.db import models
from cms.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'CMSPlugin.publisher_is_draft'
        db.add_column('cms_cmsplugin', 'publisher_is_draft', orm['cms.cmsplugin:publisher_is_draft'])
        
        # Adding field 'Page.publisher_is_draft'
        db.add_column('cms_page', 'publisher_is_draft', orm['cms.page:publisher_is_draft'])
        
        # Adding field 'Page.publisher_state'
        db.add_column('cms_page', 'publisher_state', orm['cms.page:publisher_state'])
        
        # Adding field 'Title.publisher_public'
        db.add_column('cms_title', 'publisher_public', orm['cms.title:publisher_public'])
        
        # Adding field 'Title.publisher_is_draft'
        db.add_column('cms_title', 'publisher_is_draft', orm['cms.title:publisher_is_draft'])
        
        # Adding field 'Title.publisher_state'
        db.add_column('cms_title', 'publisher_state', orm['cms.title:publisher_state'])
        
        # Adding field 'CMSPlugin.publisher_state'
        db.add_column('cms_cmsplugin', 'publisher_state', orm['cms.cmsplugin:publisher_state'])
        
        # Adding field 'Page.publisher_public'
        db.add_column('cms_page', 'publisher_public', orm['cms.page:publisher_public'])
        
        # Adding field 'CMSPlugin.publisher_public'
        db.add_column('cms_cmsplugin', 'publisher_public', orm['cms.cmsplugin:publisher_public'])
        
        # Deleting field 'Page.public'
        db.delete_column('cms_page', 'public_id')
        
        # Deleting field 'Title.public'
        db.delete_column('cms_title', 'public_id')
        
        # Deleting field 'CMSPlugin.inherited_public'
        db.delete_column('cms_cmsplugin', 'inherited_public_id')
        
        # Deleting model 'titlepublic'
        db.delete_table('cms_titlepublic')
        
        # Deleting model 'cmspluginpublic'
        db.delete_table('cms_cmspluginpublic')
        
        # Deleting model 'pagepublic'
        db.delete_table('cms_pagepublic')
       
        # Creating unique_together for [publisher_is_draft, language, page] on Title.
        db.create_unique('cms_title', ['publisher_is_draft', 'language', 'page_id'])
       
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'CMSPlugin.publisher_is_draft'
        db.delete_column('cms_cmsplugin', 'publisher_is_draft')
        
        # Deleting field 'Page.publisher_is_draft'
        db.delete_column('cms_page', 'publisher_is_draft')
        
        # Deleting field 'Page.publisher_state'
        db.delete_column('cms_page', 'publisher_state')
        
        # Deleting field 'Title.publisher_public'
        db.delete_column('cms_title', 'publisher_public_id')
        
        # Deleting field 'Title.publisher_is_draft'
        db.delete_column('cms_title', 'publisher_is_draft')
        
        # Deleting field 'Title.publisher_state'
        db.delete_column('cms_title', 'publisher_state')
        
        # Deleting field 'CMSPlugin.publisher_state'
        db.delete_column('cms_cmsplugin', 'publisher_state')
        
        # Deleting field 'Page.publisher_public'
        db.delete_column('cms_page', 'publisher_public_id')
        
        # Deleting field 'CMSPlugin.publisher_public'
        db.delete_column('cms_cmsplugin', 'publisher_public_id')
        
        # Adding field 'Page.public'
        db.add_column('cms_page', 'public', orm['cms.page:public'])
        
        # Adding field 'Title.public'
        db.add_column('cms_title', 'public', orm['cms.title:public'])
        
        # Adding field 'CMSPlugin.inherited_public'
        db.add_column('cms_cmsplugin', 'inherited_public', orm['cms.cmsplugin:inherited_public'])
        
       
        
        # Adding model 'titlepublic'
        db.create_table('cms_titlepublic', (
            ('menu_title', orm['cms.cmsplugin:menu_title']),
            ('meta_description', orm['cms.cmsplugin:meta_description']),
            ('slug', orm['cms.cmsplugin:slug']),
            ('meta_keywords', orm['cms.cmsplugin:meta_keywords']),
            ('page_title', orm['cms.cmsplugin:page_title']),
            ('language', orm['cms.cmsplugin:language']),
            ('application_urls', orm['cms.cmsplugin:application_urls']),
            ('has_url_overwrite', orm['cms.cmsplugin:has_url_overwrite']),
            ('redirect', orm['cms.cmsplugin:redirect']),
            ('mark_delete', orm['cms.cmsplugin:mark_delete']),
            ('creation_date', orm['cms.cmsplugin:creation_date']),
            ('title', orm['cms.cmsplugin:title']),
            ('path', orm['cms.cmsplugin:path']),
            ('id', orm['cms.cmsplugin:id']),
            ('page', orm['cms.cmsplugin:page']),
        ))
        db.send_create_signal('cms', ['titlepublic'])
        
        # Adding model 'cmspluginpublic'
        db.create_table('cms_cmspluginpublic', (
            ('rght', orm['cms.cmsplugin:rght']),
            ('parent', orm['cms.cmsplugin:parent']),
            ('language', orm['cms.cmsplugin:language']),
            ('level', orm['cms.cmsplugin:level']),
            ('mark_delete', orm['cms.cmsplugin:mark_delete']),
            ('creation_date', orm['cms.cmsplugin:creation_date']),
            ('lft', orm['cms.cmsplugin:lft']),
            ('tree_id', orm['cms.cmsplugin:tree_id']),
            ('position', orm['cms.cmsplugin:position']),
            ('plugin_type', orm['cms.cmsplugin:plugin_type']),
            ('placeholder', orm['cms.cmsplugin:placeholder']),
            ('id', orm['cms.cmsplugin:id']),
            ('page', orm['cms.cmsplugin:page']),
        ))
        db.send_create_signal('cms', ['cmspluginpublic'])
        
        # Adding model 'pagepublic'
        db.create_table('cms_pagepublic', (
            ('rght', orm['cms.cmsplugin:rght']),
            ('navigation_extenders', orm['cms.cmsplugin:navigation_extenders']),
            ('site', orm['cms.cmsplugin:site']),
            ('creation_date', orm['cms.cmsplugin:creation_date']),
            ('lft', orm['cms.cmsplugin:lft']),
            ('in_navigation', orm['cms.cmsplugin:in_navigation']),
            ('id', orm['cms.cmsplugin:id']),
            ('reverse_id', orm['cms.cmsplugin:reverse_id']),
            ('login_required', orm['cms.cmsplugin:login_required']),
            ('created_by', orm['cms.cmsplugin:created_by']),
            ('publication_end_date', orm['cms.cmsplugin:publication_end_date']),
            ('moderator_state', orm['cms.cmsplugin:moderator_state']),
            ('template', orm['cms.cmsplugin:template']),
            ('tree_id', orm['cms.cmsplugin:tree_id']),
            ('parent', orm['cms.cmsplugin:parent']),
            ('soft_root', orm['cms.cmsplugin:soft_root']),
            ('publication_date', orm['cms.cmsplugin:publication_date']),
            ('level', orm['cms.cmsplugin:level']),
            ('changed_by', orm['cms.cmsplugin:changed_by']),
            ('mark_delete', orm['cms.cmsplugin:mark_delete']),
            ('published', orm['cms.cmsplugin:published']),
        ))
        db.send_create_signal('cms', ['pagepublic'])
        
        # Deleting unique_together for [publisher_is_draft, language, page] on Title.
        db.delete_unique('cms_title', ['publisher_is_draft', 'language', 'page_id'])
        
        # Creating unique_together for [language, page] on title.
        db.create_unique('cms_title', ['language', 'page_id'])
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'cms.cmsplugin': {
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.cmspluginpublic': {
            'creation_date': 'django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 7, 6, 3, 45, 1, 471918))',
            'id': 'django.db.models.fields.AutoField(primary_key=True)',
            'language': 'django.db.models.fields.CharField(max_length=5, db_index=True)',
            'level': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'lft': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'mark_delete': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'page': "django.db.models.fields.related.ForeignKey(to=orm['cms.PagePublic'])",
            'parent': "django.db.models.fields.related.ForeignKey(to=orm['cms.CMSPluginPublic'], null=True, blank=True)",
            'placeholder': 'django.db.models.fields.CharField(max_length=50, db_index=True)',
            'plugin_type': 'django.db.models.fields.CharField(max_length=50, db_index=True)',
            'position': 'django.db.models.fields.PositiveSmallIntegerField(null=True, blank=True)',
            'rght': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'tree_id': 'django.db.models.fields.PositiveIntegerField(db_index=True)'
        },
        'cms.globalpagepermission': {
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change_advanced_settings': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_recover_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'cms.page': {
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagemoderator': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderate_children': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderate_descendants': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderate_page': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'cms.pagemoderatorstate': {
            'action': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'cms.pagepermission': {
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change_advanced_settings': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'grant_on': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'cms.pagepublic': {
            'changed_by': 'django.db.models.fields.CharField(max_length=70)',
            'created_by': 'django.db.models.fields.CharField(max_length=70)',
            'creation_date': 'django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 7, 6, 3, 45, 2, 307614))',
            'id': 'django.db.models.fields.AutoField(primary_key=True)',
            'in_navigation': 'django.db.models.fields.BooleanField(default=True, blank=True, db_index=True)',
            'level': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'lft': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'login_required': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'mark_delete': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'moderator_state': 'django.db.models.fields.SmallIntegerField(default=1, blank=True)',
            'navigation_extenders': 'django.db.models.fields.CharField(blank=True, max_length=80, null=True, db_index=True)',
            'parent': "django.db.models.fields.related.ForeignKey(related_name='children', null=True, to=orm['cms.PagePublic'], blank=True)",
            'publication_date': 'django.db.models.fields.DateTimeField(blank=True, null=True, db_index=True)',
            'publication_end_date': 'django.db.models.fields.DateTimeField(blank=True, null=True, db_index=True)',
            'published': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'reverse_id': 'django.db.models.fields.CharField(blank=True, max_length=40, null=True, db_index=True)',
            'rght': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'site': "django.db.models.fields.related.ForeignKey(to=orm['sites.Site'])",
            'soft_root': 'django.db.models.fields.BooleanField(default=False, blank=True, db_index=True)',
            'template': 'django.db.models.fields.CharField(max_length=100)',
            'tree_id': 'django.db.models.fields.PositiveIntegerField(db_index=True)'
        },
        'cms.pageuser': {
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_users'", 'to': "orm['auth.User']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.pageusergroup': {
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_usergroups'", 'to': "orm['auth.User']"}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.publiccmsplugin': {
            'creation_date': 'django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 7, 1, 3, 12, 55, 766462))',
            'id': 'django.db.models.fields.AutoField(primary_key=True, blank=True)',
            'language': 'django.db.models.fields.CharField(max_length=5, db_index=True)',
            'level': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'lft': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'mark_delete': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'page': "django.db.models.fields.related.ForeignKey(to=orm['cms.PublicPage'])",
            'parent': "django.db.models.fields.related.ForeignKey(to=orm['cms.PublicCMSPlugin'], null=True, blank=True)",
            'placeholder': 'django.db.models.fields.CharField(max_length=50, db_index=True)',
            'plugin_type': 'django.db.models.fields.CharField(max_length=50, db_index=True)',
            'position': 'django.db.models.fields.PositiveSmallIntegerField(null=True, blank=True)',
            'rght': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'tree_id': 'django.db.models.fields.PositiveIntegerField(db_index=True)'
        },
        'cms.publicpage': {
            'changed_by': 'django.db.models.fields.CharField(max_length=70)',
            'created_by': 'django.db.models.fields.CharField(max_length=70)',
            'creation_date': 'django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 7, 1, 3, 12, 53, 158243))',
            'id': 'django.db.models.fields.AutoField(primary_key=True, blank=True)',
            'in_navigation': 'django.db.models.fields.BooleanField(default=True, blank=True, db_index=True)',
            'level': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'lft': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'login_required': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'mark_delete': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'moderator_state': 'django.db.models.fields.SmallIntegerField(default=1, blank=True)',
            'navigation_extenders': 'django.db.models.fields.CharField(blank=True, max_length=80, null=True, db_index=True)',
            'parent': "django.db.models.fields.related.ForeignKey(related_name='children', null=True, to=orm['cms.PublicPage'], blank=True)",
            'publication_date': 'django.db.models.fields.DateTimeField(blank=True, null=True, db_index=True)',
            'publication_end_date': 'django.db.models.fields.DateTimeField(blank=True, null=True, db_index=True)',
            'published': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'reverse_id': 'django.db.models.fields.CharField(blank=True, max_length=40, null=True, db_index=True)',
            'rght': 'django.db.models.fields.PositiveIntegerField(db_index=True)',
            'site': "django.db.models.fields.related.ForeignKey(to=orm['sites.Site'])",
            'soft_root': 'django.db.models.fields.BooleanField(default=False, blank=True, db_index=True)',
            'template': 'django.db.models.fields.CharField(max_length=100)',
            'tree_id': 'django.db.models.fields.PositiveIntegerField(db_index=True)'
        },
        'cms.title': {
            'Meta': {'unique_together': "(('publisher_is_draft', 'language', 'page'),)"},
            'application_urls': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'has_url_overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'menu_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'title_set'", 'to': "orm['cms.Page']"}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Title']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'redirect': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms.titlepublic': {
            'application_urls': 'django.db.models.fields.CharField(blank=True, max_length=200, null=True, db_index=True)',
            'creation_date': 'django.db.models.fields.DateTimeField(default=datetime.datetime(2009, 7, 6, 3, 45, 1, 69773))',
            'has_url_overwrite': 'django.db.models.fields.BooleanField(default=False, blank=True, db_index=True)',
            'id': 'django.db.models.fields.AutoField(primary_key=True)',
            'language': 'django.db.models.fields.CharField(max_length=5, db_index=True)',
            'mark_delete': 'django.db.models.fields.BooleanField(default=False, blank=True)',
            'menu_title': 'django.db.models.fields.CharField(max_length=255, null=True, blank=True)',
            'meta_description': 'django.db.models.fields.TextField(max_length=255, null=True, blank=True)',
            'meta_keywords': 'django.db.models.fields.CharField(max_length=255, null=True, blank=True)',
            'page': "django.db.models.fields.related.ForeignKey(related_name='title_set', to=orm['cms.PagePublic'])",
            'page_title': 'django.db.models.fields.CharField(max_length=255, null=True, blank=True)',
            'path': 'django.db.models.fields.CharField(max_length=255, db_index=True)',
            'redirect': 'django.db.models.fields.CharField(max_length=255, null=True, blank=True)',
            'slug': 'django.db.models.fields.SlugField(max_length=255, db_index=True)',
            'title': 'django.db.models.fields.CharField(max_length=255)'
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }
    
    complete_apps = ['cms']
