# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Example1'
        db.create_table(u'placeholderapp_example1', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_3', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_4', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date_field', self.gf('django.db.models.fields.DateField')(null=True)),
            ('placeholder', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
        ))
        db.send_create_signal(u'placeholderapp', ['Example1'])

        # Adding model 'TwoPlaceholderExample'
        db.create_table(u'placeholderapp_twoplaceholderexample', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_3', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_4', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='p1', null=True, to=orm['cms.Placeholder'])),
            ('placeholder_2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='p2', null=True, to=orm['cms.Placeholder'])),
        ))
        db.send_create_signal(u'placeholderapp', ['TwoPlaceholderExample'])

        # Adding model 'DynamicPlaceholderSlotExample'
        db.create_table(u'placeholderapp_dynamicplaceholderslotexample', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dynamic_pl_1', null=True, to=orm['cms.Placeholder'])),
            ('placeholder_2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dynamic_pl_2', null=True, to=orm['cms.Placeholder'])),
        ))
        db.send_create_signal(u'placeholderapp', ['DynamicPlaceholderSlotExample'])

        # Adding model 'CharPksExample'
        db.create_table(u'placeholderapp_charpksexample', (
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255, primary_key=True)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='charpk_p1', null=True, to=orm['cms.Placeholder'])),
        ))
        db.send_create_signal(u'placeholderapp', ['CharPksExample'])

        # Adding model 'MultilingualExample1Translation'
        db.create_table(u'placeholderapp_multilingualexample1_translation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('master', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', null=True, to=orm['placeholderapp.MultilingualExample1'])),
        ))
        db.send_create_signal(u'placeholderapp', ['MultilingualExample1Translation'])

        # Adding unique constraint on 'MultilingualExample1Translation', fields ['language_code', 'master']
        db.create_unique(u'placeholderapp_multilingualexample1_translation', ['language_code', 'master_id'])

        # Adding model 'MultilingualExample1'
        db.create_table(u'placeholderapp_multilingualexample1', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
        ))
        db.send_create_signal(u'placeholderapp', ['MultilingualExample1'])


    def backwards(self, orm):
        # Removing unique constraint on 'MultilingualExample1Translation', fields ['language_code', 'master']
        db.delete_unique(u'placeholderapp_multilingualexample1_translation', ['language_code', 'master_id'])

        # Deleting model 'Example1'
        db.delete_table(u'placeholderapp_example1')

        # Deleting model 'TwoPlaceholderExample'
        db.delete_table(u'placeholderapp_twoplaceholderexample')

        # Deleting model 'DynamicPlaceholderSlotExample'
        db.delete_table(u'placeholderapp_dynamicplaceholderslotexample')

        # Deleting model 'CharPksExample'
        db.delete_table(u'placeholderapp_charpksexample')

        # Deleting model 'MultilingualExample1Translation'
        db.delete_table(u'placeholderapp_multilingualexample1_translation')

        # Deleting model 'MultilingualExample1'
        db.delete_table(u'placeholderapp_multilingualexample1')


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
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'})
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