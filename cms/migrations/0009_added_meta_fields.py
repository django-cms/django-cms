# -*- coding: utf-8 -*-
from south.db import db
from django.db import models
from cms.models import *
import datetime

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Title.meta_keywords'
        db.add_column('cms_title', 'meta_keywords', models.CharField(_("keywords"), max_length=255, blank=True, null=True))
        
        # Adding field 'Title.meta_description'
        db.add_column('cms_title', 'meta_description', models.TextField(_("description"), max_length=255, blank=True, null=True))        
    
    def backwards(self, orm):
        
        # Deleting field 'Title.meta_keywords'
        db.delete_column('cms_title', 'meta_keywords')
        
        # Deleting field 'Title.meta_description'
        db.delete_column('cms_title', 'meta_description')
        
    
    models = {
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'db_table': "'django_site'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.pagepermission': {
            'can_change_softroot': ('models.BooleanField', ['_("can change soft-root")'], {'default': 'False'}),
            'can_edit': ('models.BooleanField', ['_("can edit")'], {'default': 'True'}),
            'can_publish': ('models.BooleanField', ['_("can publish")'], {'default': 'True'}),
            'everybody': ('models.BooleanField', ['_("everybody")'], {'default': 'False'}),
            'group': ('models.ForeignKey', ['Group'], {'null': 'True', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'page': ('models.ForeignKey', ['Page'], {'null': 'True', 'blank': 'True'}),
            'type': ('models.IntegerField', ['_("type")'], {'default': '0'}),
            'user': ('models.ForeignKey', ['User'], {'null': 'True', 'blank': 'True'})
        },
        'cms.title': {
            'Meta': {'unique_together': "(('language','page'),)"},
            'application_urls': ('models.CharField', ["_('application')"], {'blank': 'True', 'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'creation_date': ('models.DateTimeField', ['_("creation date")'], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'has_url_overwrite': ('models.BooleanField', ['_("has url overwrite")'], {'default': 'False', 'editable': 'False', 'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', ['_("language")'], {'max_length': '3', 'db_index': 'True'}),
            'meta_description': ('models.TextField', ['_("description")'], {'max_length': '255', 'blank': 'True', 'null':'True'}),
            'meta_keywords': ('models.CharField', ['_("keywords")'], {'max_length': '255', 'blank': 'True', 'null':'True'}),
            'page': ('models.ForeignKey', ['Page'], {'related_name': '"title_set"'}),
            'path': ('models.CharField', ['_("path")'], {'max_length': '255', 'db_index': 'True'}),
            'redirect': ('models.CharField', ['_("redirect")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('models.SlugField', ['_("slug")'], {'unique': 'False', 'max_length': '255', 'db_index': 'True'}),
            'title': ('models.CharField', ['_("title")'], {'max_length': '255'})
        },
        'cms.cmsplugin': {
            'creation_date': ('models.DateTimeField', ['_("creation date")'], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', ['_("language")'], {'db_index': 'True', 'max_length': '3', 'editable': 'False', 'blank': 'False'}),
            'level': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'}),
            'lft': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'}),
            'page': ('models.ForeignKey', ['Page'], {'editable': 'False'}),
            'parent': ('models.ForeignKey', ['CMSPlugin'], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'placeholder': ('models.CharField', ['_("slot")'], {'max_length': '50', 'editable': 'False', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', ['_("plugin_name")'], {'max_length': '50', 'editable': 'False', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', ['_("position")'], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'}),
            'tree_id': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            'author': ('models.ForeignKey', ['User'], {'limit_choices_to': "{'page__isnull':False}"}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', ['_("in navigation")'], {'default': 'True', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'}),
            'lft': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'}),
            'login_required': ('models.BooleanField', ["_('login required')"], {'default': 'False'}),
            'navigation_extenders': ('models.CharField', ['_("navigation extenders")'], {'blank': 'True', 'max_length': '80', 'null': 'True', 'db_index': 'True'}),
            'parent': ('models.ForeignKey', ['Page'], {'db_index': 'True', 'related_name': "'children'", 'null': 'True', 'blank': 'True'}),
            'publication_date': ('models.DateTimeField', ['_("publication date")'], {'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', ['_("publication end date")'], {'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'reverse_id': ('models.CharField', ['_("id")'], {'blank': 'True', 'max_length': '40', 'null': 'True', 'db_index': 'True'}),
            'rght': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'}),
            'sites': ('models.ManyToManyField', ['Site'], {}),
            'soft_root': ('models.BooleanField', ['_("soft root")'], {'default': 'False', 'db_index': 'True'}),
            'status': ('models.IntegerField', ['_("status")'], {'default': '0', 'db_index': 'True'}),
            'template': ('models.CharField', ['_("template")'], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [],{'db_index':'True', 'editable':'False'})
        },
        'auth.group': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['cms']
