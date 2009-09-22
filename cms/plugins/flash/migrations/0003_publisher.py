
from south.db import db
from django.db import models
from cms.plugins.flash.models import *

class Migration:
    
    depends_on = (
        ("cms", "0012_publisher"),
    )
    
    needed_by = (
        ("cms", "0019_public_table_renames"),
    )

    def forwards(self, orm):
        
        # Adding model 'PublicFlash'
        db.create_table('flash_publicflash', (
            ('width', orm['flash.publicflash:width']),
            ('height', orm['flash.publicflash:height']),
            ('mark_delete', orm['flash.publicflash:mark_delete']),
            ('file', orm['flash.publicflash:file']),
            ('publiccmsplugin_ptr', orm['flash.publicflash:publiccmsplugin_ptr']),
        ))
        db.send_create_signal('flash', ['PublicFlash'])
        
        # Adding field 'Flash.public'
        db.add_column('flash_flash', 'public', orm['flash.flash:public'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicFlash'
        db.delete_table('flash_publicflash')
        
        # Deleting field 'Flash.public'
        db.delete_column('flash_flash', 'public_id')
        
    
    
    models = {
        'flash.flash': {
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('models.FileField', [], {'max_length': '100'}),
            'height': ('models.CharField', [], {'max_length': '6'}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['flash.PublicFlash']"}),
            'width': ('models.CharField', [], {'max_length': '6'})
        },
        'cms.publiccmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.publicpage': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.page': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'flash.publicflash': {
            'file': ('models.FileField', [], {'max_length': '100'}),
            'height': ('models.CharField', [], {'max_length': '6'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publiccmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'width': ('models.CharField', [], {'max_length': '6'})
        }
    }
    
    complete_apps = ['flash']
