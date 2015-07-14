# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Example1.publish'
        db.add_column(u'placeholderapp_example1', 'publish',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Example1.publish'
        db.delete_column(u'placeholderapp_example1', 'publish')


    models = {
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'placeholderapp.charpksexample': {
            'Meta': {'object_name': 'CharPksExample'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charpk_p1'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'primary_key': 'True'})
        },
        u'placeholderapp.dynamicplaceholderslotexample': {
            'Meta': {'object_name': 'DynamicPlaceholderSlotExample'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dynamic_pl_1'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'placeholder_2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dynamic_pl_2'", 'null': 'True', 'to': "orm['cms.Placeholder']"})
        },
        u'placeholderapp.example1': {
            'Meta': {'object_name': 'Example1'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_3': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_4': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_field': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'publish': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'placeholderapp.multilingualexample1': {
            'Meta': {'object_name': 'MultilingualExample1'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'})
        },
        u'placeholderapp.multilingualexample1translation': {
            'Meta': {'unique_together': "[('language_code', 'master')]", 'object_name': 'MultilingualExample1Translation', 'db_table': "u'placeholderapp_multilingualexample1_translation'"},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'null': 'True', 'to': u"orm['placeholderapp.MultilingualExample1']"})
        },
        u'placeholderapp.twoplaceholderexample': {
            'Meta': {'object_name': 'TwoPlaceholderExample'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_3': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_4': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'p1'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'placeholder_2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'p2'", 'null': 'True', 'to': "orm['cms.Placeholder']"})
        }
    }

    complete_apps = ['placeholderapp']