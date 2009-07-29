
from south.db import db
from django.db import models
from cms.plugins.text.models import *

class Migration:
    
    depends_on = (
        ("cms", "0005_mptt_added_to_plugins"),
    )
    
    def forwards(self, orm):
        
        # Adding model 'Text'
        db.create_table('text_text', (
            ('body', models.TextField(_("body"))),
            ('cmsplugin_ptr', models.OneToOneField(orm['cms.CMSPlugin'])),
        ))
        db.send_create_signal('text', ['Text'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Text'
        db.delete_table('text_text')
        
    
    
    models = {
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    
