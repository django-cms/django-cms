
from south.db import db
from django.db import models
from cms.plugins.picture.models import *

class Migration:
    
    depends_on = (
        ("cms", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Picture'
        db.create_table('picture_picture', (
            ('link', models.CharField(_("link"), max_length=255, null=True, blank=True)),
            ('image', models.ImageField(_("image"), upload_to=CMSPlugin.get_media_path)),
            ('cmsplugin_ptr', models.OneToOneField(orm['cms.CMSPlugin'])),
            ('alt', models.CharField(_("alternate text"), max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('picture', ['Picture'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Picture'
        db.delete_table('picture_picture')
        
    
    
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
    
    
