# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'CacheKey'
        db.create_table('menus_cachekey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('site', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('menus', ['CacheKey'])


    def backwards(self, orm):
        
        # Deleting model 'CacheKey'
        db.delete_table('menus_cachekey')


    models = {
        'menus.cachekey': {
            'Meta': {'object_name': 'CacheKey'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['menus']
