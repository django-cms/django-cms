
from south.db import db
from django.db import models
from cms.plugins.link.models import *

class Migration:
    
    def forwards(self, orm):
        db.rename_column("link_link", "page_id", "page_link_id")
    
    
    def backwards(self, orm):
        db.rename_column("link_link", "page_link_id", "page_id")
    
    
    models = {
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'link.link': {
            'Meta': {'_bases': ['cms.models.CMSPlugin']},
            'cmsplugin_ptr': ('models.OneToOneField', ['CMSPlugin'], {}),
            'name': ('models.CharField', ['_("name")'], {'max_length': '40'}),
            'page_link': ('models.ForeignKey', ['Page'], {'null': 'True', 'verbose_name': '_("page")', 'blank': 'True'}),
            'url': ('models.URLField', ['_("link")'], {'blank': 'True', 'null': 'True', 'verify_exists': 'True'})
        }
    }
    
    complete_apps = ['link', 'page']
