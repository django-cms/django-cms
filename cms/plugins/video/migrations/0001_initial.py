
from south.db import db
from django.db import models
from cms.plugins.video.models import *

class Migration:
    
    depends_on = (
        ("cms", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Video'
        db.create_table('cmsplugin_video', (
            ('cmsplugin_ptr', orm['video.Video:cmsplugin_ptr']),
            ('movie', orm['video.Video:movie']),
            ('image', orm['video.Video:image']),
            ('width', orm['video.Video:width']),
            ('height', orm['video.Video:height']),
            ('auto_load', orm['video.Video:auto_load']),
            ('auto_play', orm['video.Video:auto_play']),
            ('loop', orm['video.Video:loop']),
            ('volume', orm['video.Video:volume']),
            ('click_url', orm['video.Video:click_url']),
            ('click_target', orm['video.Video:click_target']),
            ('bgcolor', orm['video.Video:bgcolor']),
            ('fullscreen', orm['video.Video:fullscreen']),
            ('wmode', orm['video.Video:wmode']),
            ('flash_menu', orm['video.Video:flash_menu']),
        ))
        db.send_create_signal('video', ['Video'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Video'
        db.delete_table('cmsplugin_video')
        
    
    
    models = {
        'cms.cmsplugin': {
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'page': ('models.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'parent': ('models.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'publisher_is_draft': ('models.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('models.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'publisher_state': ('models.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.page': {
            'changed_by': ('models.CharField', [], {'max_length': '70'}),
            'created_by': ('models.CharField', [], {'max_length': '70'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'menu_login_required': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('models.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('models.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publication_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publisher_is_draft': ('models.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('models.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publisher_state': ('models.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reverse_id': ('models.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('models.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('models.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('models.CharField', [], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('models.CharField', [], {'max_length': '100'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '50'})
        },
        'video.video': {
            'Meta': {'db_table': "'cmsplugin_video'"},
            'auto_load': ('models.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'auto_play': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'bgcolor': ('models.CharField', [], {'default': "'000000'", 'max_length': '6'}),
            'click_target': ('models.CharField', [], {'default': "'_blank'", 'max_length': '7'}),
            'click_url': ('models.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'flash_menu': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'fullscreen': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'height': ('models.CharField', [], {'max_length': '6'}),
            'image': ('models.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'loop': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'movie': ('models.FileField', [], {'max_length': '100'}),
            'volume': ('models.SmallIntegerField', [], {'default': '50'}),
            'width': ('models.CharField', [], {'max_length': '6'}),
            'wmode': ('models.CharField', [], {'default': "'opaque'", 'max_length': '10'})
        }
    }
    
    complete_apps = ['video']
