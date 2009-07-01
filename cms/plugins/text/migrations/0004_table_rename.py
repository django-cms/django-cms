
from south.db import db
from django.db import models
from cms.plugins.text.models import *

class Migration:
    
    def forwards(self, orm):    
        db.rename_table("text_text", "cmsplugin_text")
        db.rename_table("text_publictext", "cmsplugin_textpublic")
        
    
    
    def backwards(self, orm):       
        db.rename_table("cmsplugin_text", "text_text")
        db.rename_table("cmsplugin_textpublic", "text_publictext")
        
    
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
        'cms.page': {
            '_stub': True,
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'text.publictext': {
            'body': ('django.db.models.fields.TextField', [], {}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publiccmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'})
        },
        'text.text': {
            'body': ('django.db.models.fields.TextField', [], {}),
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['text.PublicText']"})
        }
    }
    
    complete_apps = ['text']
