# -*- coding: utf-8 -*-
from south.db import db
from django.db import models
from cms.models import *
import datetime
class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'CMSPlugin'
        db.create_table('cms_cmsplugin', (
            ('language', models.CharField(_("language"), db_index=True, max_length=3, editable=False, blank=False)),
            ('page', models.ForeignKey(orm.Page, editable=False, verbose_name=_("page"))),
            ('position', models.PositiveSmallIntegerField(_("position"), default=0, editable=False)),
            ('creation_date', models.DateTimeField(_("creation date"), default=datetime.datetime.now, editable=False)),
            ('placeholder', models.CharField(_("slot"), max_length=50, editable=False, db_index=True)),
            ('id', models.AutoField(primary_key=True)),
            ('plugin_type', models.CharField(_("plugin_name"), max_length=50, editable=False, db_index=True)),
        ))
        db.send_create_signal('cms', ['CMSPlugin'])
        
        # Adding model 'Title'
        db.create_table('cms_title', (
            ('language', models.CharField(_("language"), max_length=3, db_index=True)),
            ('title', models.CharField(_("title"), max_length=255)),
            ('page', models.ForeignKey(orm.Page, related_name="title_set", verbose_name=_("page"))),
            ('id', models.AutoField(primary_key=True)),
            ('path', models.CharField(_("path"), max_length=255, db_index=True)),
            ('creation_date', models.DateTimeField(_("creation date"), default=datetime.datetime.now, editable=False)),
            ('slug', models.SlugField(_("slug"), unique=False, max_length=255, db_index=True)),
        ))
        db.send_create_signal('cms', ['Title'])
        
        # Adding model 'PagePermission'
        db.create_table('cms_pagepermission', (
            ('everybody', models.BooleanField(_("everybody"), default=False)),
            ('can_edit', models.BooleanField(_("can edit"), default=True)),
            ('group', models.ForeignKey(orm['auth.Group'], null=True, verbose_name=_("group"), blank=True)),
            ('can_publish', models.BooleanField(_("can publish"), default=True)),
            ('page', models.ForeignKey(orm.Page, null=True, verbose_name=_("page"), blank=True)),
            ('user', models.ForeignKey(orm['auth.User'], null=True, verbose_name=_("user"), blank=True)),
            ('type', models.IntegerField(_("type"), default=0)),
            ('id', models.AutoField(primary_key=True)),
            ('can_change_softroot', models.BooleanField(_("can change soft-root"), default=False)),
        ))
        db.send_create_signal('cms', ['PagePermission'])
        
        # Adding model 'Page'
        db.create_table('cms_page', (
            ('status', models.IntegerField(_("status"), default=0, db_index=True)),
            ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
            ('level', models.PositiveIntegerField(db_index=True, editable=False)),
            ('navigation_extenders', models.CharField(_("navigation extenders"), blank=True, max_length=80, null=True, db_index=True)),
            ('has_url_overwrite', models.BooleanField(_("has url overwrite"), default=False, db_index=True)),
            ('url_overwrite', models.CharField(_("url overwrite"), blank=True, max_length=80, null=True, db_index=True)),
            ('parent', models.ForeignKey(orm.Page, db_index=True, related_name='children', null=True, editable=False, blank=True)),
            ('author', models.ForeignKey(orm['auth.User'], limit_choices_to={'page__isnull':False}, verbose_name=_("author"))),
            ('reverse_id', models.CharField(_("reverse url id"), blank=True, max_length=40, null=True, db_index=True)),
            ('login_required', models.BooleanField(_('login required'), default=False)),
            ('soft_root', models.BooleanField(_("soft root"), default=False, db_index=True)),
            ('creation_date', models.DateTimeField(default=datetime.datetime.now, editable=False)),
            ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
            ('publication_end_date', models.DateTimeField(_("publication end date"), null=True, db_index=True, blank=True)),
            ('template', models.CharField(_("template"), max_length=100)),
            ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
            ('publication_date', models.DateTimeField(_("publication date"), null=True, db_index=True, blank=True)),
            ('in_navigation', models.BooleanField(_("in navigation"), default=True, db_index=True)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('cms', ['Page'])
        
        # Adding model 'Placeholder'
        db.create_table('cms_placeholder', (
            ('body', models.TextField()),
            ('language', models.CharField(_("language"), db_index=True, max_length=3, editable=False, blank=False)),
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(_("slot"), max_length=50, editable=False, db_index=True)),
            ('page', models.ForeignKey(orm.Page, editable=False, verbose_name=_("page"))),
        ))
        db.send_create_signal('cms', ['Placeholder'])
        
        # Adding ManyToManyField 'Page.sites'
        db.create_table('cms_page_sites', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(Page, null=False)),
            ('site', models.ForeignKey(Site, null=False))
        ))
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'CMSPlugin'
        db.delete_table('cms_cmsplugin')
        
        # Deleting model 'Title'
        db.delete_table('cms_title')
        
        # Deleting model 'PagePermission'
        db.delete_table('cms_pagepermission')
        
        # Deleting model 'Page'
        db.delete_table('cms_page')
        
        # Deleting model 'Placeholder'
        db.delete_table('cms_placeholder')
        
        # Dropping ManyToManyField 'Page.sites'
        db.delete_table('cms_page_sites')
        
    
    
    models = {
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'db_table': "'django_site'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'auth.group': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    
