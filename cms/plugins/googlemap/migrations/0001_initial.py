
from south.db import db
from django.db import models
from cms.plugins.googlemap.models import *

class Migration:
    depends_on = (
        ("cms", "0012_publisher"),
    )
    
    needed_by = (
        ("cms", "0019_public_table_renames"),
    )

    
    def forwards(self, orm):
        
        # Adding model 'PublicGoogleMap'
        db.create_table('googlemap_publicgooglemap', (
            ('city', orm['googlemap.PublicGoogleMap:city']),
            ('title', orm['googlemap.PublicGoogleMap:title']),
            ('streetnr', orm['googlemap.PublicGoogleMap:streetnr']),
            ('mark_delete', orm['googlemap.PublicGoogleMap:mark_delete']),
            ('zoom', orm['googlemap.PublicGoogleMap:zoom']),
            ('publiccmsplugin_ptr', orm['googlemap.PublicGoogleMap:publiccmsplugin_ptr']),
            ('content', orm['googlemap.PublicGoogleMap:content']),
            ('street', orm['googlemap.PublicGoogleMap:street']),
            ('postcode', orm['googlemap.PublicGoogleMap:postcode']),
        ))
        db.send_create_signal('googlemap', ['PublicGoogleMap'])
        
        # Adding model 'GoogleMap'
        db.create_table('googlemap_googlemap', (
            ('city', orm['googlemap.GoogleMap:city']),
            ('title', orm['googlemap.GoogleMap:title']),
            ('streetnr', orm['googlemap.GoogleMap:streetnr']),
            ('cmsplugin_ptr', orm['googlemap.GoogleMap:cmsplugin_ptr']),
            ('zoom', orm['googlemap.GoogleMap:zoom']),
            ('content', orm['googlemap.GoogleMap:content']),
            ('street', orm['googlemap.GoogleMap:street']),
            ('postcode', orm['googlemap.GoogleMap:postcode']),
            ('public', orm['googlemap.GoogleMap:public']),
        ))
        db.send_create_signal('googlemap', ['GoogleMap'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicGoogleMap'
        db.delete_table('googlemap_publicgooglemap')
        
        # Deleting model 'GoogleMap'
        db.delete_table('googlemap_googlemap')
        
    
    
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
        'googlemap.publicgooglemap': {
            'city': ('models.CharField', [], {'max_length': '100'}),
            'content': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'postcode': ('models.IntegerField', [], {}),
            'publiccmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.PublicCMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'street': ('models.CharField', [], {'max_length': '100'}),
            'streetnr': ('models.IntegerField', [], {}),
            'title': ('models.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zoom': ('models.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cms.page': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'googlemap.googlemap': {
            'city': ('models.CharField', [], {'max_length': '100'}),
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'content': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'postcode': ('models.IntegerField', [], {}),
            'public': ('models.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['googlemap.PublicGoogleMap']"}),
            'street': ('models.CharField', [], {'max_length': '100'}),
            'streetnr': ('models.IntegerField', [], {}),
            'title': ('models.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zoom': ('models.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['googlemap']
