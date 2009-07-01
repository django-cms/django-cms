
from south.db import db
from django.db import models
from cms.plugins.flash.models import *

class Migration:
    
    def forwards(self, orm):
        
        db.rename_table("flash_flash", "cmsplugin_flash")
        db.rename_table("flash_publicflash", "cmsplugin_flashpublic")
        
    
    
    def backwards(self, orm):
        
        db.rename_table("cmsplugin_flash", "flash_flash")
        db.rename_table("cmsplugin_flashpublic", "flash_publicflash")
        
    
    
    models = {
        'flash.flash': {
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['flash.PublicFlash']"}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
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
        'flash.publicflash': {
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publiccmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        }
    }
    
    complete_apps = ['flash']
