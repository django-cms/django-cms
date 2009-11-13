
from south.db import db
from django.db import models
from cms.plugins.teaser.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting field 'Teaser.public'
        db.delete_column('cmsplugin_teaser', 'public_id')
        
        # Deleting model 'teaserpublic'
        db.delete_table('cmsplugin_teaserpublic')
        
    
    
    def backwards(self, orm):
        
        # Adding field 'Teaser.public'
        db.add_column('cmsplugin_teaser', 'public', orm['teaser.teaser:public'])
        
        # Adding model 'teaserpublic'
        db.create_table('cmsplugin_teaserpublic', (
            ('description', orm['teaser.TeaserPublic:description']),
            ('title', orm['teaser.TeaserPublic:title']),
            ('url', orm['teaser.TeaserPublic:url']),
            ('image', orm['teaser.TeaserPublic:image']),
            ('mark_delete', orm['teaser.TeaserPublic:mark_delete']),
            ('page_link', orm['teaser.TeaserPublic:page_link']),
            ('cmspluginpublic_ptr', orm['teaser.TeaserPublic:cmspluginpublic_ptr']),
        ))
        db.send_create_signal('teaser', ['teaserpublic'])
        
    
    
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
            'publisher_is_draft': ('models.BooleanField', [], {'default': '1', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('models.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'publisher_state': ('models.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.cmspluginpublic': {
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 3, 6, 52, 32, 344027)'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('models.ForeignKey', [], {'to': "orm['cms.PagePublic']"}),
            'parent': ('models.ForeignKey', [], {'to': "orm['cms.CMSPluginPublic']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'moderator_state': ('models.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('models.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publication_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'publisher_is_draft': ('models.BooleanField', [], {'default': '1', 'db_index': 'True', 'blank': 'True'}),
            'publisher_public': ('models.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publisher_state': ('models.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reverse_id': ('models.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('models.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('models.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('models.CharField', [], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagepublic': {
            'changed_by': ('models.CharField', [], {'max_length': '70'}),
            'created_by': ('models.CharField', [], {'max_length': '70'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 3, 6, 52, 33, 599060)'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', [], {'default': 'True', 'blank': 'True', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mark_delete': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('models.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', [], {'blank': 'True', 'max_length': '80', 'null': 'True', 'db_index': 'True'}),
            'parent': ('models.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['cms.PagePublic']", 'blank': 'True'}),
            'publication_date': ('models.DateTimeField', [], {'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'publication_end_date': ('models.DateTimeField', [], {'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'published': ('models.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('models.CharField', [], {'blank': 'True', 'max_length': '40', 'null': 'True', 'db_index': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('models.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('models.BooleanField', [], {'default': 'False', 'blank': 'True', 'db_index': 'True'}),
            'template': ('models.CharField', [], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('models.CharField', [], {'max_length': '100'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '50'})
        },
        'teaser.teaser': {
            'Meta': {'db_table': "'cmsplugin_teaser'"},
            'cmsplugin_ptr': ('models.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('models.TextField', [], {'null': 'True', 'blank': 'True'}),
            'image': ('models.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'page_link': ('models.ForeignKey', [], {'to': "orm['cms.Page']", 'null': 'True', 'blank': 'True'}),
            'title': ('models.CharField', [], {'max_length': '255'}),
            'url': ('models.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'teaser.teaserpublic': {
            'cmspluginpublic_ptr': "models.OneToOneField(to=orm['cms.CMSPluginPublic'], unique=True, primary_key=True)",
            'description': 'models.TextField(null=True, blank=True)',
            'image': 'models.ImageField(max_length=100, null=True, blank=True)',
            'mark_delete': 'models.BooleanField(default=False, blank=True)',
            'page_link': "models.ForeignKey(to=orm['cms.PagePublic'], null=True, blank=True)",
            'title': 'models.CharField(max_length=255)',
            'url': 'models.CharField(max_length=255, null=True, blank=True)'
        }
    }
    
    complete_apps = ['teaser']
