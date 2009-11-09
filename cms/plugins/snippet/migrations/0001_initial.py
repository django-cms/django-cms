
from south.db import db
from django.db import models
from cms.plugins.snippet.models import *

class Migration:
    
    depends_on = (
        ("cms", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Snippet'
        db.create_table('snippet_snippet', (
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(_("name"), unique=True, max_length=255)),
            ('html', models.TextField(_("HTML"), blank=True)),
        ))
        db.send_create_signal('snippet', ['Snippet'])
        
        # Adding model 'SnippetPtr'
        db.create_table('snippet_snippetptr', (
            ('cmsplugin_ptr', models.OneToOneField(orm['cms.CMSPlugin'])),
            ('snippet', models.ForeignKey(orm.Snippet)),
        ))
        db.send_create_signal('snippet', ['SnippetPtr'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Snippet'
        db.delete_table('snippet_snippet')
        
        # Deleting model 'SnippetPtr'
        db.delete_table('snippet_snippetptr')
        
    
    
    models = {
        'snippet.snippet': {
            'html': ('models.TextField', ['_("HTML")'], {'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', ['_("name")'], {'unique': 'True', 'max_length': '255'})
        },
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'snippet.snippetptr': {
            'Meta': {'_bases': ['cms.models.CMSPlugin']},
            'cmsplugin_ptr': ('models.OneToOneField', ["orm['cms.CMSPlugin']"], {}),
            'snippet': ('models.ForeignKey', ["orm['snippet.Snippet']"], {})
        }
    }
    
    complete_apps = ['snippet']
