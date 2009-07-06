
from south.db import db
from django.db import models
from cms.plugins.text.models import *

class Migration:
    
    depends_on = (
        ("cms", "0012_publisher"),
    )

    def forwards(self, orm):
        
        # Adding model 'PublicText'
        db.create_table('text_publictext', (
            ('body', orm['text.publictext:body']),
            ('mark_delete', orm['text.publictext:mark_delete']),
            ('publiccmsplugin_ptr', orm['text.publictext:publiccmsplugin_ptr']),
        ))
        db.send_create_signal('text', ['PublicText'])
        
        # Adding field 'Text.public'
        db.add_column('text_text', 'public', orm['text.text:public'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicText'
        db.delete_table('text_publictext')
        
        # Deleting field 'Text.public'
        db.delete_column('text_text', 'public_id')
        
    
    
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
