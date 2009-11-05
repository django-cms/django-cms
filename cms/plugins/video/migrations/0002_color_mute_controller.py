
from south.db import db
from django.db import models
from cms.plugins.video.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Video.mute'
        db.add_column('cmsplugin_video', 'mute', orm['video.video:mute'])
        
        # Adding field 'Video.controller_style'
        db.add_column('cmsplugin_video', 'controller_style', orm['video.video:controller_style'])
        
        # Adding field 'Video.mute_only'
        db.add_column('cmsplugin_video', 'mute_only', orm['video.video:mute_only'])
        
        # Adding field 'Video.fgcolor'
        db.add_column('cmsplugin_video', 'fgcolor', orm['video.video:fgcolor'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Video.mute'
        db.delete_column('cmsplugin_video', 'mute')
        
        # Deleting field 'Video.controller_style'
        db.delete_column('cmsplugin_video', 'controller_style')
        
        # Deleting field 'Video.mute_only'
        db.delete_column('cmsplugin_video', 'mute_only')
        
        # Deleting field 'Video.fgcolor'
        db.delete_column('cmsplugin_video', 'fgcolor')
        
    
    
    models = {
        'cms.cmsplugin': {
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.page': {
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'menu_login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'video.video': {
            'Meta': {'db_table': "'cmsplugin_video'"},
            'auto_load': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'auto_play': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'bgcolor': ('django.db.models.fields.CharField', [], {'default': "'000000'", 'max_length': '6'}),
            'click_target': ('django.db.models.fields.CharField', [], {'default': "'_blank'", 'max_length': '7'}),
            'click_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'controller_style': ('django.db.models.fields.CharField', [], {'default': "'dock'", 'max_length': '7'}),
            'fgcolor': ('django.db.models.fields.CharField', [], {'default': "'13abec'", 'max_length': '6'}),
            'flash_menu': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'fullscreen': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'loop': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'movie': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'mute': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mute_only': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'volume': ('django.db.models.fields.SmallIntegerField', [], {'default': '50'}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'wmode': ('django.db.models.fields.CharField', [], {'default': "'opaque'", 'max_length': '10'})
        }
    }
    
    complete_apps = ['video']
