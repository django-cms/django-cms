# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Example1'
        db.create_table('placeholderapp_example1', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_3', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_4', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date_field', self.gf('django.db.models.fields.DateField')(null=True)),
            ('placeholder', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
            ('publish', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('decimal_field', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=1, blank=True)),
        ))
        db.send_create_signal('placeholderapp', ['Example1'])

        # Adding model 'TwoPlaceholderExample'
        db.create_table('placeholderapp_twoplaceholderexample', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_3', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_4', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='p1', null=True, to=orm['cms.Placeholder'])),
            ('placeholder_2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='p2', null=True, to=orm['cms.Placeholder'])),
        ))
        db.send_create_signal('placeholderapp', ['TwoPlaceholderExample'])

        # Adding model 'DynamicPlaceholderSlotExample'
        db.create_table('placeholderapp_dynamicplaceholderslotexample', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dynamic_pl_1', null=True, to=orm['cms.Placeholder'])),
            ('placeholder_2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dynamic_pl_2', null=True, to=orm['cms.Placeholder'])),
        ))
        db.send_create_signal('placeholderapp', ['DynamicPlaceholderSlotExample'])

        # Adding model 'CharPksExample'
        db.create_table('placeholderapp_charpksexample', (
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255, primary_key=True)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='charpk_p1', null=True, to=orm['cms.Placeholder'])),
        ))
        db.send_create_signal('placeholderapp', ['CharPksExample'])

        # Adding model 'MultilingualExample1Translation'
        db.create_table('placeholderapp_multilingualexample1_translation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('char_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('char_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('master', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', null=True, to=orm['placeholderapp.MultilingualExample1'])),
        ))
        db.send_create_signal('placeholderapp', ['MultilingualExample1Translation'])

        # Adding unique constraint on 'MultilingualExample1Translation', fields ['language_code', 'master']
        db.create_unique('placeholderapp_multilingualexample1_translation', ['language_code', 'master_id'])

        # Adding model 'MultilingualExample1'
        db.create_table('placeholderapp_multilingualexample1', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('placeholder_1', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
        ))
        db.send_create_signal('placeholderapp', ['MultilingualExample1'])


    def backwards(self, orm):
        # Removing unique constraint on 'MultilingualExample1Translation', fields ['language_code', 'master']
        db.delete_unique('placeholderapp_multilingualexample1_translation', ['language_code', 'master_id'])

        # Deleting model 'Example1'
        db.delete_table('placeholderapp_example1')

        # Deleting model 'TwoPlaceholderExample'
        db.delete_table('placeholderapp_twoplaceholderexample')

        # Deleting model 'DynamicPlaceholderSlotExample'
        db.delete_table('placeholderapp_dynamicplaceholderslotexample')

        # Deleting model 'CharPksExample'
        db.delete_table('placeholderapp_charpksexample')

        # Deleting model 'MultilingualExample1Translation'
        db.delete_table('placeholderapp_multilingualexample1_translation')

        # Deleting model 'MultilingualExample1'
        db.delete_table('placeholderapp_multilingualexample1')


    models = {
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'placeholderapp.charpksexample': {
            'Meta': {'object_name': 'CharPksExample'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charpk_p1'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'primary_key': 'True'})
        },
        'placeholderapp.dynamicplaceholderslotexample': {
            'Meta': {'object_name': 'DynamicPlaceholderSlotExample'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dynamic_pl_1'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'placeholder_2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dynamic_pl_2'", 'null': 'True', 'to': "orm['cms.Placeholder']"})
        },
        'placeholderapp.example1': {
            'Meta': {'object_name': 'Example1'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_3': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_4': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_field': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'decimal_field': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'publish': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'placeholderapp.multilingualexample1': {
            'Meta': {'unique_together': '()', 'object_name': 'MultilingualExample1'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'})
        },
        'placeholderapp.multilingualexample1translation': {
            'Meta': {'unique_together': "[('language_code', 'master')]", 'object_name': 'MultilingualExample1Translation', 'db_table': "'placeholderapp_multilingualexample1_translation'"},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'null': 'True', 'to': "orm['placeholderapp.MultilingualExample1']"})
        },
        'placeholderapp.twoplaceholderexample': {
            'Meta': {'object_name': 'TwoPlaceholderExample'},
            'char_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_3': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'char_4': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'placeholder_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'p1'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'placeholder_2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'p2'", 'null': 'True', 'to': "orm['cms.Placeholder']"})
        }
    }

    complete_apps = ['placeholderapp']