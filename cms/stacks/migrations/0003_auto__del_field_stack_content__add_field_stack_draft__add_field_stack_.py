# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Stack.content'
        db.rename_column('stacks_stack', 'content_id', 'draft_id')

        # Adding field 'Stack.public'
        db.add_column(u'stacks_stack', 'public',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='stacks_public', null=True, to=orm['cms.Placeholder']),
                      keep_default=False)

        # Adding field 'Stack.dirty'
        db.add_column(u'stacks_stack', 'dirty',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

    def backwards(self, orm):

        db.rename_column('stacks_stack', 'draft_id', 'content_id')        # Adding field 'Stack.content'

        # Deleting field 'Stack.public'
        db.delete_column(u'stacks_stack', 'public_id')

        # Deleting field 'Stack.dirty'
        db.delete_column(u'stacks_stack', 'dirty')


    models = {
        'cms.cmsplugin': {
            'Meta': {'object_name': 'CMSPlugin'},
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        u'stacks.stack': {
            'Meta': {'object_name': 'Stack'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'creation_method': ('django.db.models.fields.CharField', [], {'default': "'code'", 'max_length': '20', 'blank': 'True'}),
            'dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'draft': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stacks_draft'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'public': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stacks_public'", 'null': 'True', 'to': "orm['cms.Placeholder']"})
        },
        u'stacks.stacklink': {
            'Meta': {'object_name': 'StackLink', 'db_table': "u'cmsplugin_stacklink'", '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'stack': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'linked_plugins'", 'to': u"orm['stacks.Stack']"})
        }
    }

    complete_apps = ['stacks']