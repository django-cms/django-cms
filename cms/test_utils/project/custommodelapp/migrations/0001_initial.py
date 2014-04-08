# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Publisher'
        db.create_table(u'custommodelapp_publisher', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=30)),
            ('published', self.gf('django.db.models.fields.BooleanField')()),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('zip_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('presentation', self.gf('djangocms_text_ckeditor.fields.HTMLField')()),
        ))
        db.send_create_signal(u'custommodelapp', ['Publisher'])

        # Adding model 'Author'
        db.create_table(u'custommodelapp_author', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('published', self.gf('django.db.models.fields.BooleanField')()),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('is_alive', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'custommodelapp', ['Author'])

        # Adding model 'Book'
        db.create_table(u'custommodelapp_book', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100)),
            ('published', self.gf('django.db.models.fields.BooleanField')()),
            ('publisher', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['custommodelapp.Publisher'])),
            ('publication_date', self.gf('django.db.models.fields.DateField')()),
            ('still_published', self.gf('django.db.models.fields.DateField')()),
            ('public_domain', self.gf('django.db.models.fields.DateField')()),
            ('summary', self.gf('djangocms_text_ckeditor.fields.HTMLField')()),
            ('description', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
        ))
        db.send_create_signal(u'custommodelapp', ['Book'])

        # Adding M2M table for field authors on 'Book'
        m2m_table_name = db.shorten_name(u'custommodelapp_book_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('book', models.ForeignKey(orm[u'custommodelapp.book'], null=False)),
            ('author', models.ForeignKey(orm[u'custommodelapp.author'], null=False))
        ))
        db.create_unique(m2m_table_name, ['book_id', 'author_id'])


    def backwards(self, orm):
        # Deleting model 'Publisher'
        db.delete_table(u'custommodelapp_publisher')

        # Deleting model 'Author'
        db.delete_table(u'custommodelapp_author')

        # Deleting model 'Book'
        db.delete_table(u'custommodelapp_book')

        # Removing M2M table for field authors on 'Book'
        db.delete_table(db.shorten_name(u'custommodelapp_book_authors'))


    models = {
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        u'custommodelapp.author': {
            'Meta': {'ordering': "['last_name', 'first_name']", 'object_name': 'Author'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_alive': ('django.db.models.fields.BooleanField', [], {}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'published': ('django.db.models.fields.BooleanField', [], {})
        },
        u'custommodelapp.book': {
            'Meta': {'ordering': "['-publication_date']", 'object_name': 'Book'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['custommodelapp.Author']", 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public_domain': ('django.db.models.fields.DateField', [], {}),
            'publication_date': ('django.db.models.fields.DateField', [], {}),
            'published': ('django.db.models.fields.BooleanField', [], {}),
            'publisher': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['custommodelapp.Publisher']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100'}),
            'still_published': ('django.db.models.fields.DateField', [], {}),
            'summary': ('djangocms_text_ckeditor.fields.HTMLField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'custommodelapp.publisher': {
            'Meta': {'ordering': "['name']", 'object_name': 'Publisher'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'presentation': ('djangocms_text_ckeditor.fields.HTMLField', [], {}),
            'published': ('django.db.models.fields.BooleanField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '30'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['custommodelapp']