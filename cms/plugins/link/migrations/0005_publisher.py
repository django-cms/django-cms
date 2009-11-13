
from south.db import db
from django.db import models
from cms.plugins.link.models import *

class Migration:
    
    depends_on = (
        ("cms", "0012_publisher"),
    )

    needed_by = (
        ("cms", "0019_public_table_renames"),
    )

    def forwards(self, orm):
        
        # Adding model 'PublicLink'
        db.create_table('link_publiclink', (
            ('url', orm['link.publiclink:url']),
            ('page_link', orm['link.publiclink:page_link']),
            ('mark_delete', orm['link.publiclink:mark_delete']),
            ('name', orm['link.publiclink:name']),
            ('publiccmsplugin_ptr', orm['link.publiclink:publiccmsplugin_ptr']),
        ))
        db.send_create_signal('link', ['PublicLink'])
        
        # Adding field 'Link.public'
        db.add_column('link_link', 'public', orm['link.link:public'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicLink'
        db.delete_table('link_publiclink')
        
        # Deleting field 'Link.public'
        db.delete_column('link_link', 'public_id')
        
    
    
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
        'link.link': {
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '256'}),
            'page_link': ('models.ForeignKey', [], {'to': "orm['cms.Page']", 'null': 'True', 'blank': 'True'}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['link.PublicLink']"}),
            'url': ('models.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'link.publiclink': {
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('models.CharField', [], {'max_length': '256'}),
            'page_link': ('models.ForeignKey', [], {'to': "orm['cms.PublicPage']", 'null': 'True', 'blank': 'True'}),
            'publiccmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('models.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'cms.page': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['link']
