
from south.db import db
from django.db import models
from cms.plugins.file.models import *

class Migration:
    
    depends_on = (
        ("cms", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'File'
        db.create_table('file_file', (
            ('cmsplugin_ptr', models.OneToOneField(orm['cms.CMSPlugin'])),
            ('file', models.FileField(_("file"), upload_to=CMSPlugin.get_media_path)),
            ('title', models.CharField(_("title"), max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('file', ['File'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'File'
        db.delete_table('file_file')
        
    
    
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
    
    
