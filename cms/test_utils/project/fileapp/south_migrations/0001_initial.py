# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FileModel'
        db.create_table(u'fileapp_filemodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('test_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'fileapp', ['FileModel'])


    def backwards(self, orm):
        # Deleting model 'FileModel'
        db.delete_table(u'fileapp_filemodel')


    models = {
        u'fileapp.filemodel': {
            'Meta': {'object_name': 'FileModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'test_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fileapp']