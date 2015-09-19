# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PluginModelWithFKFromModel'
        db.create_table(u'manytomany_rel_pluginmodelwithfkfrommodel', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'manytomany_rel', ['PluginModelWithFKFromModel'])

        # Adding model 'FKModel'
        db.create_table(u'manytomany_rel_fkmodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fk_field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['manytomany_rel.PluginModelWithFKFromModel'])),
        ))
        db.send_create_signal(u'manytomany_rel', ['FKModel'])

        # Adding model 'PluginModelWithM2MToModel'
        db.create_table(u'manytomany_rel_pluginmodelwithm2mtomodel', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'manytomany_rel', ['PluginModelWithM2MToModel'])

        # Adding M2M table for field m2m_field on 'PluginModelWithM2MToModel'
        m2m_table_name = db.shorten_name(u'manytomany_rel_pluginmodelwithm2mtomodel_m2m_field')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pluginmodelwithm2mtomodel', models.ForeignKey(orm[u'manytomany_rel.pluginmodelwithm2mtomodel'], null=False)),
            ('m2mtargetmodel', models.ForeignKey(orm[u'manytomany_rel.m2mtargetmodel'], null=False))
        ))
        db.create_unique(m2m_table_name, ['pluginmodelwithm2mtomodel_id', 'm2mtargetmodel_id'])

        # Adding model 'M2MTargetModel'
        db.create_table(u'manytomany_rel_m2mtargetmodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'manytomany_rel', ['M2MTargetModel'])

        # Adding model 'M2MTargetPluginModel'
        db.create_table(u'manytomany_rel_m2mtargetpluginmodel', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'manytomany_rel', ['M2MTargetPluginModel'])

        # Adding model 'PluginModelWithM2MToPlugin'
        db.create_table(u'manytomany_rel_pluginmodelwithm2mtoplugin', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'manytomany_rel', ['PluginModelWithM2MToPlugin'])

        # Adding M2M table for field m2m_field on 'PluginModelWithM2MToPlugin'
        m2m_table_name = db.shorten_name(u'manytomany_rel_pluginmodelwithm2mtoplugin_m2m_field')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pluginmodelwithm2mtoplugin', models.ForeignKey(orm[u'manytomany_rel.pluginmodelwithm2mtoplugin'], null=False)),
            ('m2mtargetpluginmodel', models.ForeignKey(orm[u'manytomany_rel.m2mtargetpluginmodel'], null=False))
        ))
        db.create_unique(m2m_table_name, ['pluginmodelwithm2mtoplugin_id', 'm2mtargetpluginmodel_id'])

        # Adding model 'PluginModelWithFKFromPlugin'
        db.create_table(u'manytomany_rel_pluginmodelwithfkfromplugin', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'manytomany_rel', ['PluginModelWithFKFromPlugin'])

        # Adding model 'FKPluginModel'
        db.create_table(u'manytomany_rel_fkpluginmodel', (
            (u'cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('fk_field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['manytomany_rel.PluginModelWithFKFromPlugin'])),
        ))
        db.send_create_signal(u'manytomany_rel', ['FKPluginModel'])


    def backwards(self, orm):
        # Deleting model 'PluginModelWithFKFromModel'
        db.delete_table(u'manytomany_rel_pluginmodelwithfkfrommodel')

        # Deleting model 'FKModel'
        db.delete_table(u'manytomany_rel_fkmodel')

        # Deleting model 'PluginModelWithM2MToModel'
        db.delete_table(u'manytomany_rel_pluginmodelwithm2mtomodel')

        # Removing M2M table for field m2m_field on 'PluginModelWithM2MToModel'
        db.delete_table(db.shorten_name(u'manytomany_rel_pluginmodelwithm2mtomodel_m2m_field'))

        # Deleting model 'M2MTargetModel'
        db.delete_table(u'manytomany_rel_m2mtargetmodel')

        # Deleting model 'M2MTargetPluginModel'
        db.delete_table(u'manytomany_rel_m2mtargetpluginmodel')

        # Deleting model 'PluginModelWithM2MToPlugin'
        db.delete_table(u'manytomany_rel_pluginmodelwithm2mtoplugin')

        # Removing M2M table for field m2m_field on 'PluginModelWithM2MToPlugin'
        db.delete_table(db.shorten_name(u'manytomany_rel_pluginmodelwithm2mtoplugin_m2m_field'))

        # Deleting model 'PluginModelWithFKFromPlugin'
        db.delete_table(u'manytomany_rel_pluginmodelwithfkfromplugin')

        # Deleting model 'FKPluginModel'
        db.delete_table(u'manytomany_rel_fkpluginmodel')


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
        u'manytomany_rel.fkmodel': {
            'Meta': {'object_name': 'FKModel'},
            'fk_field': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['manytomany_rel.PluginModelWithFKFromModel']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'manytomany_rel.fkpluginmodel': {
            'Meta': {'object_name': 'FKPluginModel', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'fk_field': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['manytomany_rel.PluginModelWithFKFromPlugin']"})
        },
        u'manytomany_rel.m2mtargetmodel': {
            'Meta': {'object_name': 'M2MTargetModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'manytomany_rel.m2mtargetpluginmodel': {
            'Meta': {'object_name': 'M2MTargetPluginModel', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'manytomany_rel.pluginmodelwithfkfrommodel': {
            'Meta': {'object_name': 'PluginModelWithFKFromModel', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'manytomany_rel.pluginmodelwithfkfromplugin': {
            'Meta': {'object_name': 'PluginModelWithFKFromPlugin', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'manytomany_rel.pluginmodelwithm2mtomodel': {
            'Meta': {'object_name': 'PluginModelWithM2MToModel', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'm2m_field': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['manytomany_rel.M2MTargetModel']", 'symmetrical': 'False'})
        },
        u'manytomany_rel.pluginmodelwithm2mtoplugin': {
            'Meta': {'object_name': 'PluginModelWithM2MToPlugin', '_ormbases': ['cms.CMSPlugin']},
            u'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'm2m_field': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['manytomany_rel.M2MTargetPluginModel']", 'symmetrical': 'False'})
        },
        u'manytomany_rel.section': {
            'Meta': {'object_name': 'Section'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['manytomany_rel']