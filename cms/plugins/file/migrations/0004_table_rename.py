
from south.db import db
from django.db import models
from cms.plugins.file.models import *

class Migration:
    depends_on = (
        ("cms", "0019_public_table_renames"),
    )
    def forwards(self, orm):
        
        db.rename_table("file_file", "cmsplugin_file")
        db.rename_table("file_publicfile", "cmsplugin_filepublic")
        db.rename_column("cmsplugin_filepublic", "publiccmsplugin_ptr_id", "cmspluginpublic_ptr_id")
        db.alter_column('cmsplugin_file', 'public_id', orm['file.file:public'])
        try:
            db.delete_foreign_key('cmsplugin_file' ,'public_id')
        except:
            pass
        db.drop_primary_key("cmsplugin_filepublic")
        db.create_primary_key("cmsplugin_filepublic", ("cmspluginpublic_ptr_id",))
        db.foreign_key_sql('cmsplugin_file' ,'public_id', 'cmsplugin_filepublic', 'cmspluginpublic_ptr_id')
    
    def backwards(self, orm):
        try:
            db.delete_foreign_key('cmsplugin_file' ,'public_id')
        except:
            pass
        db.drop_primary_key("cmsplugin_filepublic")
        db.rename_column("cmsplugin_filepublic", "cmspluginpublic_ptr_id", "publiccmsplugin_ptr_id")
        db.create_primary_key("cmsplugin_filepublic", ("publiccmsplugin_ptr_id",))
        db.rename_table("cmsplugin_file", "file_file")
        db.rename_table("cmsplugin_filepublic", "file_publicfile")
        db.alter_column('file_file', 'public_id', orm['file.file:public'])
    
    
    models = {
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('models.CharField', [], {'max_length': '100'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '50'})
        },
        'file.filepublic': {
            'Meta': {'db_table': "'cmsplugin_filepublic'"},
            'cmspluginpublic_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPluginPublic']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('models.FileField', [], {'max_length': '100'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'title': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'file.file': {
            'Meta': {'db_table': "'cmsplugin_file'"},
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('models.FileField', [], {'max_length': '100'}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['file.FilePublic']"}),
            'title': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'auth.user': {
            'date_joined': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 53, 40, 186023)'}),
            'email': ('models.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('models.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('models.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'is_active': ('models.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 53, 40, 185915)'}),
            'last_name': ('models.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('models.CharField', [], {'max_length': '128'}),
            'user_permissions': ('models.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('models.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cms.cmsplugin': {
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 21, 57, 5675)'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'inherited_public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'inherited_origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.CMSPluginPublic']"}),
            'language': ('models.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'page': ('models.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'parent': ('models.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('models.CharField', [], {'max_length': '100'}),
            'content_type': ('models.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('models.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('models.CharField', [], {'max_length': '100'}),
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'model': ('models.CharField', [], {'max_length': '100'}),
            'name': ('models.CharField', [], {'max_length': '100'})
        },
        'cms.page': {
            'changed_by': ('models.CharField', [], {'max_length': '70'}),
            'created_by': ('models.CharField', [], {'max_length': '70'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 21, 56, 222565)'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('models.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('models.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PagePublic']"}),
            'publication_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('models.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('models.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('models.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('models.CharField', [], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'auth.group': {
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('models.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('models.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'cms.cmspluginpublic': {
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 21, 57, 374744)'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('models.ForeignKey', [], {'to': "orm['cms.PagePublic']"}),
            'parent': ('models.ForeignKey', [], {'to': "orm['cms.CMSPluginPublic']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagepublic': {
            'changed_by': ('models.CharField', [], {'max_length': '70'}),
            'created_by': ('models.CharField', [], {'max_length': '70'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 21, 56, 590962)'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('models.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('models.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.PagePublic']"}),
            'publication_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('models.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('models.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('models.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('models.CharField', [], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        }
    }
    
    complete_apps = ['file']
