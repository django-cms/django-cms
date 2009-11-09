
from south.db import db
from django.db import models
from cms.plugins.flash.models import *

class Migration:
    
    depends_on = (
        ("cms", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Flash'
        db.create_table('flash_flash', (
            ('width', models.CharField(_('width'), max_length=6)),
            ('cmsplugin_ptr', models.OneToOneField(orm['cms.CMSPlugin'])),
            ('file', models.FileField(_('file'), upload_to=CMSPlugin.get_media_path)),
            ('height', models.CharField(_('height'), max_length=6)),
        ))
        db.send_create_signal('flash', ['Flash'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Flash'
        db.delete_table('flash_flash')
        
    
    
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
    
    
