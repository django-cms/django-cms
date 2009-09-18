
from south.db import db
from django.db import models
from cms.plugins.text.models import *

class Migration:
    
    depends_on = (
        ("cms", "0012_publisher"),
    )
    
    needed_by = (
        ("cms", "0019_public_table_renames"),
    )

    def forwards(self, orm):
        
        # Adding field 'Text.public'
        db.add_column('text_text', 'public', orm['text.text:public'])
        # Adding model 'PublicText'
        db.create_table('text_publictext', (
            ('body', orm['text.publictext:body']),
            ('mark_delete', orm['text.publictext:mark_delete']),
            ('publiccmsplugin_ptr', orm['text.publictext:publiccmsplugin_ptr']),
        ))
        db.send_create_signal('text', ['PublicText'])
        
        
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicText'
        db.delete_table('text_publictext')
        
        # Deleting field 'Text.public'
        db.delete_column('text_text', 'public_id')
        
    
    
    models = {
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
        'text.publictext': {
            'body': ('models.TextField', [], {}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publiccmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'})
        },
        'text.text': {
            'body': ('models.TextField', [], {}),
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['text.PublicText']"})
        }
    }
    
    complete_apps = ['text']
