
from south.db import db
from django.db import models
from cms.plugins.picture.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'PublicPicture'
        db.create_table('picture_publicpicture', (
            ('url', orm['picture.publicpicture:url']),
            ('image', orm['picture.publicpicture:image']),
            ('mark_delete', orm['picture.publicpicture:mark_delete']),
            ('alt', orm['picture.publicpicture:alt']),
            ('publiccmsplugin_ptr', orm['picture.publicpicture:publiccmsplugin_ptr']),
        ))
        db.send_create_signal('picture', ['PublicPicture'])
        
        # Adding field 'Picture.public'
        db.add_column('picture_picture', 'public', orm['picture.picture:public'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicPicture'
        db.delete_table('picture_publicpicture')
        
        # Deleting field 'Picture.public'
        db.delete_column('picture_picture', 'public_id')
        
    
    
    models = {
        'cms.publiccmsplugin': {
            '_stub': True,
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'picture.publicpicture': {
            'alt': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publiccmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
        'picture.picture': {
            'alt': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['picture.PublicPicture']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['picture']
