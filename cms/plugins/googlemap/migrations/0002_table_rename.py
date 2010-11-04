
from south.db import db
from django.db import models
from cms.plugins.googlemap.models import *

class Migration:
    depends_on = (
        ("cms", "0019_public_table_renames"),
    )
    def forwards(self, orm):
        
        db.rename_table("googlemap_googlemap", "cmsplugin_googlemap")
        db.rename_table("googlemap_publicgooglemap", "cmsplugin_googlemappublic")
        db.rename_column("cmsplugin_googlemappublic", "publiccmsplugin_ptr_id", "cmspluginpublic_ptr_id")
        db.alter_column('cmsplugin_googlemap', 'public_id', orm['googlemap.googlemap:public'])
        try:
            db.delete_foreign_key('cmsplugin_googlemap' ,'public_id')
        except:
            pass
        db.drop_primary_key("cmsplugin_googlemappublic")
        db.create_primary_key("cmsplugin_googlemappublic", ("cmspluginpublic_ptr_id",))
        db.foreign_key_sql('cmsplugin_googlemap' ,'public_id', 'cmsplugin_googlemappublic', 'cmspluginpublic_ptr_id')
    
    def backwards(self, orm):
        db.delete_foreign_key('cmsplugin_googlemap' ,'public_id')
        db.drop_primary_key("cmsplugin_googlemappublic")
        db.rename_column("cmsplugin_googlemappublic", "cmspluginpublic_ptr_id", "publiccmsplugin_ptr_id")
        db.create_primary_key("cmsplugin_googlemappublic", ("publiccmsplugin_ptr_id",))
        db.rename_table("cmsplugin_googlemap", "googlemap_googlemap")
        db.rename_table("cmsplugin_googlemappublic", "googlemap_publicgooglemap")
        db.alter_column('googlemap_googlemap', 'public_id', orm['googlemap.googlemap:public'])
        
        
    
    models = {
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('models.CharField', [], {'max_length': '100'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '50'})
        },
        'cms.publiccmsplugin': {
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.cmsplugin': {
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 30, 24, 667806)'}),
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
        'cms.page': {
            'changed_by': ('models.CharField', [], {'max_length': '70'}),
            'created_by': ('models.CharField', [], {'max_length': '70'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 30, 25, 482037)'}),
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
        'googlemap.googlemappublic': {
            'Meta': {'db_table': "'cmsplugin_googlemappublic'"},
            'city': ('models.CharField', [], {'max_length': '100'}),
            'cmspluginpublic_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPluginPublic']", 'unique': 'True', 'primary_key': 'True'}),
            'content': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'postcode': ('models.IntegerField', [], {}),
            'street': ('models.CharField', [], {'max_length': '100'}),
            'streetnr': ('models.IntegerField', [], {}),
            'title': ('models.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zoom': ('models.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cms.pagepublic': {
            'changed_by': ('models.CharField', [], {'max_length': '70'}),
            'created_by': ('models.CharField', [], {'max_length': '70'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 30, 25, 20572)'}),
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
        },
        'googlemap.googlemap': {
            'Meta': {'db_table': "'cmsplugin_googlemap'"},
            'city': ('models.CharField', [], {'max_length': '100'}),
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'content': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'postcode': ('models.IntegerField', [], {}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['googlemap.GoogleMapPublic']"}),
            'street': ('models.CharField', [], {'max_length': '100'}),
            'streetnr': ('models.IntegerField', [], {}),
            'title': ('models.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zoom': ('models.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cms.cmspluginpublic': {
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 2, 6, 30, 25, 831777)'}),
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
        }
    }
    
    complete_apps = ['googlemap']
