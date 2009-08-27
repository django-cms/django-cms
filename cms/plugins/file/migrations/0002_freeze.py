
from south.db import db
from django.db import models
from cms.plugins.file.models import *

class Migration:
    
    def forwards(self, orm):
        "Write your forwards migration here"
    
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'file.file': {
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('models.FileField', [], {'max_length': '100'}),
            'title': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'cms.page': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['file']
