# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestPluginAlphaModel'
        db.create_table(u'mti_pluginapp_testpluginalphamodel', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('alpha', self.gf('django.db.models.fields.CharField')(default='test plugin alpha', max_length=32)),
        ))
        db.send_create_signal(u'mti_pluginapp', ['TestPluginAlphaModel'])

        # Adding model 'TestPluginBetaModel'
        db.create_table(u'mti_pluginapp_testpluginbetamodel', (
            (u'testpluginalphamodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['mti_pluginapp.TestPluginAlphaModel'], unique=True, primary_key=True)),
            ('beta', self.gf('django.db.models.fields.CharField')(default='test plugin beta', max_length=32)),
        ))
        db.send_create_signal(u'mti_pluginapp', ['TestPluginBetaModel'])


    def backwards(self, orm):
        # Deleting model 'TestPluginAlphaModel'
        db.delete_table(u'mti_pluginapp_testpluginalphamodel')

        # Deleting model 'TestPluginBetaModel'
        db.delete_table(u'mti_pluginapp_testpluginbetamodel')


    models = {
        'cms.cmsplugin': {
            'Meta': {'object_name': 'CMSPlugin'},
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'mti_pluginapp.testpluginalphamodel': {
            'Meta': {'object_name': 'TestPluginAlphaModel', '_ormbases': ['cms.CMSPlugin']},
            'alpha': ('django.db.models.fields.CharField', [], {'default': "'test plugin alpha'", 'max_length': '32'}),
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'mti_pluginapp.testpluginbetamodel': {
            'Meta': {'object_name': 'TestPluginBetaModel', '_ormbases': [u'mti_pluginapp.TestPluginAlphaModel']},
            'beta': ('django.db.models.fields.CharField', [], {'default': "'test plugin beta'", 'max_length': '32'}),
            u'testpluginalphamodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['mti_pluginapp.TestPluginAlphaModel']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['mti_pluginapp']