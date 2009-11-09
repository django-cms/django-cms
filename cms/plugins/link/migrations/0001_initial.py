
from south.db import db
from django.db import models
from cms.plugins.link.models import *

class Migration:
    
    depends_on = (
        ("cms", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Link'
        db.create_table('link_link', (
            ('link', models.URLField(_("link"), blank=True, null=True, verify_exists=True)),
            ('cmsplugin_ptr', models.OneToOneField(orm['cms.CMSPlugin'])),
            ('name', models.CharField(_("name"), max_length=40)),
            ('page', models.ForeignKey(orm['cms.Page'], null=True, verbose_name=_("page"), blank=True)),
        ))
        db.send_create_signal('link', ['Link'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Link'
        db.delete_table('link_link')
        
    
    
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
    
    
