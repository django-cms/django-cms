# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UnalteredPM'
        db.create_table(u'revdesc_unalteredpm', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'revdesc', ['UnalteredPM'])

        # Adding model 'NoRelNmePM'
        db.create_table(u'revdesc_norelnmepm', (
            ('cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, primary_key=True, to=orm['cms.CMSPlugin'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'revdesc', ['NoRelNmePM'])

        # Adding model 'NoRelQNmePM'
        db.create_table(u'revdesc_norelqnmepm', (
            ('cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'revdesc', ['NoRelQNmePM'])

        # Adding model 'CustomRelQNmePM'
        db.create_table(u'revdesc_customrelqnmepm', (
            ('cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'revdesc', ['CustomRelQNmePM'])

        # Adding model 'CustomRelNmePM'
        db.create_table(u'revdesc_customrelnmepm', (
            ('cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(related_name='reldesc_custom_reln', unique=True, primary_key=True, to=orm['cms.CMSPlugin'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'revdesc', ['CustomRelNmePM'])

        # Adding model 'CustomRelNmeAndRelQNmePM'
        db.create_table(u'revdesc_customrelnmeandrelqnmepm', (
            ('cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(related_name='reldesc_custom_reln2', unique=True, primary_key=True, to=orm['cms.CMSPlugin'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'revdesc', ['CustomRelNmeAndRelQNmePM'])


    def backwards(self, orm):
        # Deleting model 'UnalteredPM'
        db.delete_table(u'revdesc_unalteredpm')

        # Deleting model 'NoRelNmePM'
        db.delete_table(u'revdesc_norelnmepm')

        # Deleting model 'NoRelQNmePM'
        db.delete_table(u'revdesc_norelqnmepm')

        # Deleting model 'CustomRelQNmePM'
        db.delete_table(u'revdesc_customrelqnmepm')

        # Deleting model 'CustomRelNmePM'
        db.delete_table(u'revdesc_customrelnmepm')

        # Deleting model 'CustomRelNmeAndRelQNmePM'
        db.delete_table(u'revdesc_customrelnmeandrelqnmepm')


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
        u'revdesc.customrelnmeandrelqnmepm': {
            'Meta': {'object_name': 'CustomRelNmeAndRelQNmePM', '_ormbases': ['cms.CMSPlugin']},
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'reldesc_custom_reln2'", 'unique': 'True', 'primary_key': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'revdesc.customrelnmepm': {
            'Meta': {'object_name': 'CustomRelNmePM', '_ormbases': ['cms.CMSPlugin']},
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'reldesc_custom_reln'", 'unique': 'True', 'primary_key': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'revdesc.customrelqnmepm': {
            'Meta': {'object_name': 'CustomRelQNmePM', '_ormbases': ['cms.CMSPlugin']},
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'revdesc.norelnmepm': {
            'Meta': {'object_name': 'NoRelNmePM', '_ormbases': ['cms.CMSPlugin']},
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'primary_key': 'True', 'to': "orm['cms.CMSPlugin']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'revdesc.norelqnmepm': {
            'Meta': {'object_name': 'NoRelQNmePM', '_ormbases': ['cms.CMSPlugin']},
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'revdesc.unalteredpm': {
            'Meta': {'object_name': 'UnalteredPM', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['revdesc']