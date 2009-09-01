
from south.db import db
from django.db import models
from cms.plugins.text.models import *

class Migration:
    
    def forwards(self, orm):
        "Write your forwards migration here"
    
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        },
        'text.text': {
            'body': ('models.TextField', [], {}),
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.page': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['text']
