
from south.db import db
from django.db import models
from cms.plugins.link.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Link.name'
        db.alter_column('link_link', 'name', models.CharField(_("name"), max_length=256))
        
    
    def backwards(self, orm):
        
        # Changing field 'Link.name'
        db.alter_column('link_link', 'name', models.CharField(_("name"), max_length=40))
        
    
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
            'cmsplugin_ptr': ('models.OneToOneField', ["orm['cms.CMSPlugin']"], {}),
            'name': ('models.CharField', ['_("name")'], {'max_length': '256'}),
            'page_link': ('models.ForeignKey', ["orm['cms.Page']"], {'null': 'True', 'blank': 'True'}),
            'url': ('models.URLField', ['_("link")'], {'blank': 'True', 'null': 'True', 'verify_exists': 'True'})
        }
    }
    
    complete_apps = ['link']
