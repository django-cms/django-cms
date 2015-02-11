# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Article'
        db.create_table(u'manytomany_rel_article', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('section', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['manytomany_rel.Section'])),
        ))
        db.send_create_signal(u'manytomany_rel', ['Article'])

        # Adding model 'Section'
        db.create_table(u'manytomany_rel_section', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'manytomany_rel', ['Section'])

        # Adding model 'ArticlePluginModel'
        db.create_table(u'manytomany_rel_articlepluginmodel', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'manytomany_rel', ['ArticlePluginModel'])

        # Adding M2M table for field sections on 'ArticlePluginModel'
        m2m_table_name = db.shorten_name(u'manytomany_rel_articlepluginmodel_sections')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('articlepluginmodel', models.ForeignKey(orm[u'manytomany_rel.articlepluginmodel'], null=False)),
            ('section', models.ForeignKey(orm[u'manytomany_rel.section'], null=False))
        ))
        db.create_unique(m2m_table_name, ['articlepluginmodel_id', 'section_id'])


    def backwards(self, orm):
        # Deleting model 'Article'
        db.delete_table(u'manytomany_rel_article')

        # Deleting model 'Section'
        db.delete_table(u'manytomany_rel_section')

        # Deleting model 'ArticlePluginModel'
        db.delete_table(u'manytomany_rel_articlepluginmodel')

        # Removing M2M table for field sections on 'ArticlePluginModel'
        db.delete_table(db.shorten_name(u'manytomany_rel_articlepluginmodel_sections'))


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
        u'manytomany_rel.article': {
            'Meta': {'object_name': 'Article'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['manytomany_rel.Section']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'manytomany_rel.articlepluginmodel': {
            'Meta': {'object_name': 'ArticlePluginModel', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'sections': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['manytomany_rel.Section']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'manytomany_rel.section': {
            'Meta': {'object_name': 'Section'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['manytomany_rel']