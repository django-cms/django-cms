# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Placeholder.name'
        db.delete_column('column_placeholder', 'name')

        # Deleting field 'Placeholder.width'
        db.delete_column('column_placeholder', 'width')

        # Adding field 'Placeholder.slot'
        db.add_column('column_placeholder', 'slot',
                      self.gf('django.db.models.fields.CharField')(default='name', max_length=50, db_index=True),
                      keep_default=False)

        # Adding field 'Placeholder.default_width'
        db.add_column('column_placeholder', 'default_width',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True),
                      keep_default=False)


        # Changing field 'Placeholder.placeholder'
        db.alter_column('column_placeholder', 'placeholder_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Placeholder.name'
        raise RuntimeError("Cannot reverse this migration. 'Placeholder.name' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Placeholder.width'
        raise RuntimeError("Cannot reverse this migration. 'Placeholder.width' and its values cannot be restored.")
        # Deleting field 'Placeholder.slot'
        db.delete_column('column_placeholder', 'slot')

        # Deleting field 'Placeholder.default_width'
        db.delete_column('column_placeholder', 'default_width')


        # User chose to not deal with backwards NULL issues for 'Placeholder.placeholder'
        raise RuntimeError("Cannot reverse this migration. 'Placeholder.placeholder' and its values cannot be restored.")

    models = {
        'cms.cmsplugin': {
            'Meta': {'object_name': 'CMSPlugin'},
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'column.column': {
            'Meta': {'object_name': 'Column', 'db_table': "'cmsplugin_column'", '_ormbases': ['cms.CMSPlugin']},
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'num_columns': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'})
        },
        'column.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'column': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'placeholder_inlines'", 'to': "orm['column.Column']"}),
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['column']