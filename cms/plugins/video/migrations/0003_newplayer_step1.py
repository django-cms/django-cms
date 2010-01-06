from south.db import db
from django.db import models
from cms.plugins.video.models import *

class Migration:

    def forwards(self, orm):

        # Adding field 'Video._i_width'
        db.add_column('cmsplugin_video', '_i_width', orm['video.video:_i_width'])

        # Adding field 'Video.movie_url'
        db.add_column('cmsplugin_video', 'movie_url', orm['video.video:movie_url'])

        # Adding field 'Video.buttonhighlightcolor'
        db.add_column('cmsplugin_video', 'buttonhighlightcolor', orm['video.video:buttonhighlightcolor'])

        # Adding field 'Video.auto_hide'
        db.add_column('cmsplugin_video', 'auto_hide', orm['video.video:auto_hide'])

        # Adding field 'Video.seekbarcolor'
        db.add_column('cmsplugin_video', 'seekbarcolor', orm['video.video:seekbarcolor'])

        # Adding field 'Video.buttonoutcolor'
        db.add_column('cmsplugin_video', 'buttonoutcolor', orm['video.video:buttonoutcolor'])

        # Adding field 'Video.textcolor'
        db.add_column('cmsplugin_video', 'textcolor', orm['video.video:textcolor'])

        # Adding field 'Video.seekbarbgcolor'
        db.add_column('cmsplugin_video', 'seekbarbgcolor', orm['video.video:seekbarbgcolor'])

        # Adding field 'Video.loadingbarcolor'
        db.add_column('cmsplugin_video', 'loadingbarcolor', orm['video.video:loadingbarcolor'])

        # Adding field 'Video.buttonovercolor'
        db.add_column('cmsplugin_video', 'buttonovercolor', orm['video.video:buttonovercolor'])

        # Adding field 'Video._i_height'
        db.add_column('cmsplugin_video', '_i_height', orm['video.video:_i_height'])

        # Deleting field 'Video.volume'
        db.delete_column('cmsplugin_video', 'volume')

        # Deleting field 'Video.mute'
        db.delete_column('cmsplugin_video', 'mute')

        # Deleting field 'Video.click_target'
        db.delete_column('cmsplugin_video', 'click_target')

        # Deleting field 'Video.flash_menu'
        db.delete_column('cmsplugin_video', 'flash_menu')

        # Deleting field 'Video.auto_load'
        db.delete_column('cmsplugin_video', 'auto_load')

        # Deleting field 'Video.mute_only'
        db.delete_column('cmsplugin_video', 'mute_only')

        # Deleting field 'Video.wmode'
        db.delete_column('cmsplugin_video', 'wmode')

        # Deleting field 'Video.controller_style'
        db.delete_column('cmsplugin_video', 'controller_style')

        # Deleting field 'Video.fgcolor'
        db.delete_column('cmsplugin_video', 'fgcolor')

        # Deleting field 'Video.click_url'
        db.delete_column('cmsplugin_video', 'click_url')

        # Changing field 'Video.movie'
        # (to signature: django.db.models.fields.files.FileField(max_length=100, null=True, blank=True))
        db.alter_column('cmsplugin_video', 'movie', orm['video.video:movie'])



    def backwards(self, orm):

        # Deleting field 'Video._i_width'
        db.delete_column('cmsplugin_video', '_i_width')

        # Deleting field 'Video.movie_url'
        db.delete_column('cmsplugin_video', 'movie_url')

        # Deleting field 'Video.buttonhighlightcolor'
        db.delete_column('cmsplugin_video', 'buttonhighlightcolor')

        # Deleting field 'Video.auto_hide'
        db.delete_column('cmsplugin_video', 'auto_hide')

        # Deleting field 'Video.seekbarcolor'
        db.delete_column('cmsplugin_video', 'seekbarcolor')

        # Deleting field 'Video.buttonoutcolor'
        db.delete_column('cmsplugin_video', 'buttonoutcolor')

        # Deleting field 'Video.textcolor'
        db.delete_column('cmsplugin_video', 'textcolor')

        # Deleting field 'Video.seekbarbgcolor'
        db.delete_column('cmsplugin_video', 'seekbarbgcolor')

        # Deleting field 'Video.loadingbarcolor'
        db.delete_column('cmsplugin_video', 'loadingbarcolor')

        # Deleting field 'Video.buttonovercolor'
        db.delete_column('cmsplugin_video', 'buttonovercolor')

        # Deleting field 'Video._i_height'
        db.delete_column('cmsplugin_video', '_i_height')

        # Adding field 'Video.volume'
        db.add_column('cmsplugin_video', 'volume', orm['video.video:volume'])

        # Adding field 'Video.mute'
        db.add_column('cmsplugin_video', 'mute', orm['video.video:mute'])

        # Adding field 'Video.click_target'
        db.add_column('cmsplugin_video', 'click_target', orm['video.video:click_target'])

        # Adding field 'Video.flash_menu'
        db.add_column('cmsplugin_video', 'flash_menu', orm['video.video:flash_menu'])

        # Adding field 'Video.auto_load'
        db.add_column('cmsplugin_video', 'auto_load', orm['video.video:auto_load'])

        # Adding field 'Video.mute_only'
        db.add_column('cmsplugin_video', 'mute_only', orm['video.video:mute_only'])

        # Adding field 'Video.wmode'
        db.add_column('cmsplugin_video', 'wmode', orm['video.video:wmode'])

        # Adding field 'Video.controller_style'
        db.add_column('cmsplugin_video', 'controller_style', orm['video.video:controller_style'])

        # Adding field 'Video.fgcolor'
        db.add_column('cmsplugin_video', 'fgcolor', orm['video.video:fgcolor'])

        # Adding field 'Video.click_url'
        db.add_column('cmsplugin_video', 'click_url', orm['video.video:click_url'])

        # Changing field 'Video.movie'
        # (to signature: django.db.models.fields.files.FileField(max_length=100))
        db.alter_column('cmsplugin_video', 'movie', orm['video.video:movie'])



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
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['cms.Page']"}),
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
            '_i_height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            '_i_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'auto_hide': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'auto_play': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'bgcolor': ('django.db.models.fields.CharField', [], {'default': "'000000'", 'max_length': '6'}),
            'buttonhighlightcolor': ('django.db.models.fields.CharField', [], {'default': "'FFFFFF'", 'max_length': '6'}),
            'buttonoutcolor': ('django.db.models.fields.CharField', [], {'default': "'333333'", 'max_length': '6'}),
            'buttonovercolor': ('django.db.models.fields.CharField', [], {'default': "'000000'", 'max_length': '6'}),
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'fullscreen': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'loadingbarcolor': ('django.db.models.fields.CharField', [], {'default': "'828282'", 'max_length': '6'}),
            'loop': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'movie': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'movie_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'seekbarbgcolor': ('django.db.models.fields.CharField', [], {'default': "'333333'", 'max_length': '6'}),
            'seekbarcolor': ('django.db.models.fields.CharField', [], {'default': "'13ABEC'", 'max_length': '6'}),
            'textcolor': ('django.db.models.fields.CharField', [], {'default': "'FFFFFF'", 'max_length': '6'}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        }
    }

    complete_apps = ['video']
