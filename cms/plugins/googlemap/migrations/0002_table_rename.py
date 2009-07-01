
from south.db import db
from django.db import models
from cms.plugins.googlemap.models import *

class Migration:
    
    def forwards(self, orm):
        
        db.rename_table("googlemap_googlemap", "cmsplugin_googlemap")
        db.rename_table("googlemap_publicgooglemap", "cmsplugin_googlemappublic")
        
    
    
    def backwards(self, orm):
        
        db.rename_table("cmsplugin_googlemap", "googlemap_googlemap")
        db.rename_table("cmsplugin_googlemappublic", "googlemap_publicgooglemap")
        
    
        
    
    
    models = {
        'cms.publiccmsplugin': {
            '_stub': True,
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.publicpage': {
            '_stub': True,
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'googlemap.publicgooglemap': {
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.IntegerField', [], {}),
            'publiccmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'streetnr': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zoom': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cms.page': {
            '_stub': True,
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'googlemap.googlemap': {
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.IntegerField', [], {}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['googlemap.PublicGoogleMap']"}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'streetnr': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zoom': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['googlemap']
