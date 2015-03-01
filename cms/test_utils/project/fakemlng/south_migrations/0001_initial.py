# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MainModel'
        db.create_table(u'fakemlng_mainmodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'fakemlng', ['MainModel'])

        # Adding model 'Translations'
        db.create_table(u'fakemlng_translations', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('master', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fakemlng.MainModel'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('placeholder', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
        ))
        db.send_create_signal(u'fakemlng', ['Translations'])

        # Adding unique constraint on 'Translations', fields ['master', 'language_code']
        db.create_unique(u'fakemlng_translations', ['master_id', 'language_code'])


    def backwards(self, orm):
        # Removing unique constraint on 'Translations', fields ['master', 'language_code']
        db.delete_unique(u'fakemlng_translations', ['master_id', 'language_code'])

        # Deleting model 'MainModel'
        db.delete_table(u'fakemlng_mainmodel')

        # Deleting model 'Translations'
        db.delete_table(u'fakemlng_translations')


    models = {
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'fakemlng.mainmodel': {
            'Meta': {'object_name': 'MainModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fakemlng.translations': {
            'Meta': {'unique_together': "[('master', 'language_code')]", 'object_name': 'Translations'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fakemlng.MainModel']"}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'})
        }
    }

    complete_apps = ['fakemlng']