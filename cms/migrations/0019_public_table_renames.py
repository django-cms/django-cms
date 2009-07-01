
from south.db import db
from django.db import models
from cms.models import *

class Migration:
    
    def forwards(self, orm):
        
        db.rename_table("cms_publicpage", "cms_pagepublic")
        db.rename_table("cms_publictitle", "cms_titlepublic")
        db.rename_table("cms_publiccmsplugin", "cms_cmspluginpublic")

    
    def backwards(self, orm):
        db.rename_table("cms_public_page", "cms_publicpage")
        db.rename_table("cms_public_title", "cms_publictitle")
        db.rename_table("cms_public_cmsplugin", "cms_publiccmsplugin")
        
        
    
    
    models = {
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'cms.pageuser': {
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_users'", 'to': "orm['auth.User']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.publiccmsplugin': {
            'Meta': {'db_table': "'cms_public_page'"},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 55, 766462)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.PublicPage']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.PublicCMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 53, 943350)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 53, 943211)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'cms.publictitle': {
            'Meta': {'unique_together': "(('language', 'page'),)"},
            'application_urls': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 56, 141223)'}),
            'has_url_overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'menu_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'title_set'", 'to': "orm['cms.PublicPage']"}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'redirect': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms.globalpagepermission': {
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_change_softroot': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_recover_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'cms.publicpage': {
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 53, 158243)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.PublicPage']"}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagepermission': {
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_change_softroot': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'grant_on': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'cms.cmsplugin': {
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 53, 846036)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'inherited_public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'inherited_origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PublicCMSPlugin']"}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'cms.title': {
            'Meta': {'unique_together': "(('language', 'page'),)"},
            'application_urls': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 55, 156090)'}),
            'has_url_overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'menu_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'title_set'", 'to': "orm['cms.Page']"}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PublicTitle']"}),
            'redirect': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms.page': {
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 1, 3, 12, 51, 206800)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PublicPage']"}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagemoderatorstate': {
            'action': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'cms.pagemoderator': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'moderate_children': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderate_descendants': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderate_page': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'cms.pageusergroup': {
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_usergroups'", 'to': "orm['auth.User']"}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['cms']
