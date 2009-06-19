
from south.db import db
from django.db import models
from cms.models import *

class Migration:
    
    def forwards(self, orm):
        
        
        db.rename_table('cms_cmsplugin', 'cms_publiccmsplugin')
        db.add_column('cms_publiccmsplugin', 'mark_delete',())
        
        db.rename_table('cms_page', 'cms_publicpage')
        db.add_column('cms_publicpage', 'mark_delete',())
        db.delete_column('cms_publicpage', 'status')
        
        db.rename_table('cms_title', 'cms_publictitle')
        db.add_column('cms_publictitle', 'mark_delete',())
        
        db.rename_table('cms_page_sites', 'cms_publicpage_sites')
        db.rename_column('cms_publicpage_sites', 'page', 'publicpage')
        # Adding ManyToManyField 'PublicPage.sites'
        
         # Adding model 'PublicPage'
        db.create_table('cms_page', (
            ('id', models.AutoField(primary_key=True)),
            ('author', models.ForeignKey(orm['auth.User'], limit_choices_to={'page__isnull':False})),
            ('parent', models.ForeignKey(orm.PublicPage, db_index=True, related_name='children', null=True, blank=True)),
            ('creation_date', models.DateTimeField(default=datetime.datetime.now, editable=False)),
            ('publication_date', models.DateTimeField(_("publication date"), null=True, db_index=True, blank=True)),
            ('publication_end_date', models.DateTimeField(_("publication end date"), null=True, db_index=True, blank=True)),
            ('login_required', models.BooleanField(_('login required'), default=False)),
            ('in_navigation', models.BooleanField(_("in navigation"), default=True, db_index=True)),
            ('soft_root', models.BooleanField(_("soft root"), default=False, db_index=True)),
            ('reverse_id', models.CharField(_("id"), blank=True, max_length=40, null=True, db_index=True)),
            ('navigation_extenders', models.CharField(_("navigation extenders"), blank=True, max_length=80, null=True, db_index=True)),
            ('published', models.BooleanField(_("is published"), blank=True)),
            ('template', models.CharField(_("template"), max_length=100)),
            ('moderator_state', models.SmallIntegerField(_('moderator state'), default=1, blank=True)),
            ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
            ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
            ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
            ('moderator_state', models.SmallIntegerField(_('moderator state'), default=1, blank=True)),
            ('published', models.BooleanField(_("is published"), blank=True)),
        ))
        db.send_create_signal('cms', ['Page'])
        
        
        db.create_table('cms_page_sites', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm.Page, null=False)),
            ('site', models.ForeignKey(orm['sites.Site'], null=False))
        ))
        
        # Adding model 'PublicCMSPlugin'
        db.create_table('cms_cmsplugin', (
            ('id', models.AutoField(primary_key=True)),
            ('page', models.ForeignKey(orm.Page, editable=False)),
            ('parent', models.ForeignKey(orm.PublicCMSPlugin, null=True, editable=False, blank=True)),
            ('position', models.PositiveSmallIntegerField(_("position"), null=True, editable=False, blank=True)),
            ('placeholder', models.CharField(_("slot"), max_length=50, editable=False, db_index=True)),
            ('language', models.CharField(_("language"), db_index=True, max_length=5, editable=False, blank=False)),
            ('plugin_type', models.CharField(_("plugin_name"), max_length=50, editable=False, db_index=True)),
            ('creation_date', models.DateTimeField(_("creation date"), default=datetime.datetime.now, editable=False)),
            ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
            ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
            ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
        ))
        db.send_create_signal('cms', ['CMSPlugin'])
        
        
        
        # Adding model 'PublicTitle'
        db.create_table('cms_title', (
            ('id', models.AutoField(primary_key=True)),
            ('language', models.CharField(_("language"), max_length=5, db_index=True)),
            ('title', models.CharField(_("title"), max_length=255)),
            ('menu_title', models.CharField(_("title"), max_length=255, null=True, blank=True)),
            ('slug', models.SlugField(_("slug"), unique=False, max_length=255, db_index=True)),
            ('path', models.CharField(_("path"), max_length=255, db_index=True)),
            ('has_url_overwrite', models.BooleanField(_("has url overwrite"), default=False, editable=False, db_index=True)),
            ('application_urls', models.CharField(_('application'), blank=True, max_length=200, null=True, db_index=True)),
            ('redirect', models.CharField(_("redirect"), max_length=255, null=True, blank=True)),
            ('meta_description', models.TextField(_("description"), max_length=255, null=True, blank=True)),
            ('meta_keywords', models.CharField(_("keywords"), max_length=255, null=True, blank=True)),
            ('page_title', models.CharField(_("title"), max_length=255, null=True, blank=True)),
            ('page', models.ForeignKey(orm.Page, related_name="public_title_set")),
            ('creation_date', models.DateTimeField(_("creation date"), default=datetime.datetime.now, editable=False)),
        ))
        db.send_create_signal('cms', ['Title'])
        
        # Adding model 'PageUser'
        db.create_table('cms_pageuser', (
            ('user_ptr', models.OneToOneField(orm['auth.User'])),
            ('created_by', models.ForeignKey(orm['auth.User'], related_name="created_users")),
        ))
        db.send_create_signal('cms', ['PageUser'])
        # Adding model 'PageModerator'
        db.create_table('cms_pagemoderator', (
            ('id', models.AutoField(primary_key=True)),
            ('page', models.ForeignKey(orm.Page)),
            ('user', models.ForeignKey(orm['auth.User'])),
            ('moderate_page', models.BooleanField(_('Moderate page'), blank=True)),
            ('moderate_children', models.BooleanField(_('Moderate children'), blank=True)),
            ('moderate_descendants', models.BooleanField(_('Moderate descendants'), blank=True)),
        ))
        db.send_create_signal('cms', ['PageModerator'])
        
        # Adding model 'PageModeratorState'
        db.create_table('cms_pagemoderatorstate', (
            ('id', models.AutoField(primary_key=True)),
            ('page', models.ForeignKey(orm.Page)),
            ('user', models.ForeignKey(orm['auth.User'], null=True)),
            ('created', models.DateTimeField(auto_now_add=True)),
            ('action', models.CharField(blank=True, max_length=3, null=True)),
            ('message', models.TextField(default='', max_length=1000, blank=True)),
        ))
        db.send_create_signal('cms', ['PageModeratorState'])
        
        # Adding model 'PageUserGroup'
        db.create_table('cms_pageusergroup', (
            ('group_ptr', models.OneToOneField(orm['auth.Group'])),
            ('created_by', models.ForeignKey(orm['auth.User'], related_name="created_usergroups")),
        ))
        db.send_create_signal('cms', ['PageUserGroup'])
        
        # Adding fields to 'PagePermission'
        db.add_column('cms_pagepermission', 'can_delete', models.BooleanField(_("can delete"), default=True))
        db.add_column('cms_pagepermission', 'can_change_permissions', models.BooleanField(_("can change permissions"), default=False))
        db.add_column('cms_pagepermission', 'can_moderate', models.BooleanField(_("can moderate"), default=True))
        db.add_column('cms_pagepermission', 'can_add', models.BooleanField(_("can add"), default=True))
        db.add_column('cms_pagepermission', 'grant_on', models.IntegerField(_("Grant on"), default=5))
        db.add_column('cms_pagepermission', 'can_move_page', models.BooleanField(_("can move"), default=True))
        db.add_column('cms_pagepermission', 'can_change', models.BooleanField(_("can edit"), default=True))
        db.delete_column('cms_pagepermission', 'can_edit')
        db.delete_column('cms_pagepermission', 'type')
        db.delete_column('cms_pagepermission', 'everybody')
        
        
         # Adding model 'GlobalPagePermission'
        db.create_table('cms_globalpagepermission', (
            ('id', models.AutoField(primary_key=True)),
            ('user', models.ForeignKey(orm['auth.User'], null=True, blank=True)),
            ('group', models.ForeignKey(orm['auth.Group'], null=True, blank=True)),
            ('can_change', models.BooleanField(_("can edit"), default=True)),
            ('can_add', models.BooleanField(_("can add"), default=True)),
            ('can_delete', models.BooleanField(_("can delete"), default=True)),
            ('can_change_softroot', models.BooleanField(_("can change soft-root"), default=False)),
            ('can_publish', models.BooleanField(_("can publish"), default=True)),
            ('can_change_permissions', models.BooleanField(_("can change permissions"), default=False)),
            ('can_move_page', models.BooleanField(_("can move"), default=True)),
            ('can_moderate', models.BooleanField(_("can moderate"), default=True)),
        ))
        db.send_create_signal('cms', ['GlobalPagePermission']) 
        
       
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'PublicCMSPlugin'
        db.delete_table('cms_publiccmsplugin')
        
        # Deleting model 'PageUser'
        db.delete_table('cms_pageuser')
        
        # Deleting model 'PublicTitle'
        db.delete_table('cms_publictitle')
        
        # Deleting model 'GlobalPagePermission'
        db.delete_table('cms_globalpagepermission')
        
        # Deleting model 'PublicPage'
        db.delete_table('cms_publicpage')
        
        # Deleting model 'PageModerator'
        db.delete_table('cms_pagemoderator')
        
        # Deleting model 'PageModeratorState'
        db.delete_table('cms_pagemoderatorstate')
        
        # Deleting model 'PageUserGroup'
        db.delete_table('cms_pageusergroup')
        
        # Deleting field 'PagePermission.can_delete'
        db.delete_column('cms_pagepermission', 'can_delete')
        
        # Deleting field 'Page.moderator_state'
        db.delete_column('cms_page', 'moderator_state')
        
        # Deleting field 'Page.published'
        db.delete_column('cms_page', 'published')
        
        # Deleting field 'PagePermission.can_change_permissions'
        db.delete_column('cms_pagepermission', 'can_change_permissions')
        
        # Deleting field 'PagePermission.can_moderate'
        db.delete_column('cms_pagepermission', 'can_moderate')
        
        # Deleting field 'PagePermission.can_add'
        db.delete_column('cms_pagepermission', 'can_add')
        
        # Dropping ManyToManyField 'PublicPage.sites'
        db.delete_table('cms_publicpage_sites')
        
        # Deleting field 'PagePermission.grant_on'
        db.delete_column('cms_pagepermission', 'grant_on')
        
        # Deleting field 'PagePermission.can_move_page'
        db.delete_column('cms_pagepermission', 'can_move_page')
        
        # Deleting field 'PagePermission.can_change'
        db.delete_column('cms_pagepermission', 'can_change')
        
        # Adding field 'PagePermission.can_edit'
        db.add_column('cms_pagepermission', 'can_edit', models.BooleanField(_("can edit"), default=True))
        
        # Adding field 'PagePermission.type'
        db.add_column('cms_pagepermission', 'type', models.IntegerField(_("type"), default=0))
        
        # Adding field 'Page.status'
        db.add_column('cms_page', 'status', models.IntegerField(_("status"), default=0, db_index=True))
        
        # Adding field 'PagePermission.everybody'
        db.add_column('cms_pagepermission', 'everybody', models.BooleanField(_("everybody"), default=False))
        
    
    
    models = {
        'cms.publiccmsplugin': {
            'creation_date': ('models.DateTimeField', ['_("creation date")'], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', ['_("language")'], {'db_index': 'True', 'max_length': '5', 'editable': 'False', 'blank': 'False'}),
            'level': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'mark_delete': '<< PUT FIELD DEFINITION HERE >>',
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {'editable': 'False'}),
            'parent': ('models.ForeignKey', ["orm['cms.PublicCMSPlugin']"], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'placeholder': ('models.CharField', ['_("slot")'], {'max_length': '50', 'editable': 'False', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', ['_("plugin_name")'], {'max_length': '50', 'editable': 'False', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', ['_("position")'], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'tree_id': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'})
        },
        'cms.pageuser': {
            'Meta': {'_bases': ['django.contrib.auth.models.User']},
            'created_by': ('models.ForeignKey', ["orm['auth.User']"], {'related_name': '"created_users"'}),
            'user_ptr': ('models.OneToOneField', ["orm['auth.User']"], {})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'db_table': "'django_site'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.publictitle': {
            'application_urls': ('models.CharField', ["_('application')"], {'blank': 'True', 'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'creation_date': ('models.DateTimeField', ['_("creation date")'], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'has_url_overwrite': ('models.BooleanField', ['_("has url overwrite")'], {'default': 'False', 'editable': 'False', 'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', ['_("language")'], {'max_length': '5', 'db_index': 'True'}),
            'mark_delete': '<< PUT FIELD DEFINITION HERE >>',
            'menu_title': ('models.CharField', ['_("title")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('models.TextField', ['_("description")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('models.CharField', ['_("keywords")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {'related_name': '"public_title_set"'}),
            'page_title': ('models.CharField', ['_("title")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('models.CharField', ['_("path")'], {'max_length': '255', 'db_index': 'True'}),
            'redirect': ('models.CharField', ['_("redirect")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('models.SlugField', ['_("slug")'], {'unique': 'False', 'max_length': '255', 'db_index': 'True'}),
            'title': ('models.CharField', ['_("title")'], {'max_length': '255'})
        },
        'cms.globalpagepermission': {
            'can_add': ('models.BooleanField', ['_("can add")'], {'default': 'True'}),
            'can_change': ('models.BooleanField', ['_("can edit")'], {'default': 'True'}),
            'can_change_permissions': ('models.BooleanField', ['_("can change permissions")'], {'default': 'False'}),
            'can_change_softroot': ('models.BooleanField', ['_("can change soft-root")'], {'default': 'False'}),
            'can_delete': ('models.BooleanField', ['_("can delete")'], {'default': 'True'}),
            'can_moderate': ('models.BooleanField', ['_("can moderate")'], {'default': 'True'}),
            'can_move_page': ('models.BooleanField', ['_("can move")'], {'default': 'True'}),
            'can_publish': ('models.BooleanField', ['_("can publish")'], {'default': 'True'}),
            'group': ('models.ForeignKey', ["orm['auth.Group']"], {'null': 'True', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {'null': 'True', 'blank': 'True'})
        },
        'cms.publicpage': {
            'author': ('models.ForeignKey', ["orm['auth.User']"], {'limit_choices_to': "{'page__isnull':False}"}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', ['_("in navigation")'], {'default': 'True', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'login_required': ('models.BooleanField', ["_('login required')"], {'default': 'False'}),
            'mark_delete': '<< PUT FIELD DEFINITION HERE >>',
            'moderator_state': ('models.SmallIntegerField', ["_('moderator state')"], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', ['_("navigation extenders")'], {'blank': 'True', 'max_length': '80', 'null': 'True', 'db_index': 'True'}),
            'parent': ('models.ForeignKey', ["orm['cms.PublicPage']"], {'db_index': 'True', 'related_name': "'children'", 'null': 'True', 'blank': 'True'}),
            'publication_date': ('models.DateTimeField', ['_("publication date")'], {'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', ['_("publication end date")'], {'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'published': ('models.BooleanField', ['_("is published")'], {'blank': 'True'}),
            'reverse_id': ('models.CharField', ['_("id")'], {'blank': 'True', 'max_length': '40', 'null': 'True', 'db_index': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'sites': ('models.ManyToManyField', ["orm['sites.Site']"], {}),
            'soft_root': ('models.BooleanField', ['_("soft root")'], {'default': 'False', 'db_index': 'True'}),
            'template': ('models.CharField', ['_("template")'], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'})
        },
        'cms.pagepermission': {
            'can_add': ('models.BooleanField', ['_("can add")'], {'default': 'True'}),
            'can_change': ('models.BooleanField', ['_("can edit")'], {'default': 'True'}),
            'can_change_permissions': ('models.BooleanField', ['_("can change permissions")'], {'default': 'False'}),
            'can_change_softroot': ('models.BooleanField', ['_("can change soft-root")'], {'default': 'False'}),
            'can_delete': ('models.BooleanField', ['_("can delete")'], {'default': 'True'}),
            'can_moderate': ('models.BooleanField', ['_("can moderate")'], {'default': 'True'}),
            'can_move_page': ('models.BooleanField', ['_("can move")'], {'default': 'True'}),
            'can_publish': ('models.BooleanField', ['_("can publish")'], {'default': 'True'}),
            'grant_on': ('models.IntegerField', ['_("Grant on")'], {'default': '5'}),
            'group': ('models.ForeignKey', ["orm['auth.Group']"], {'null': 'True', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {'null': 'True', 'blank': 'True'}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {'null': 'True', 'blank': 'True'})
        },
        'cms.cmsplugin': {
            'creation_date': ('models.DateTimeField', ['_("creation date")'], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'inherited_public': '<< PUT FIELD DEFINITION HERE >>',
            'language': ('models.CharField', ['_("language")'], {'db_index': 'True', 'max_length': '5', 'editable': 'False', 'blank': 'False'}),
            'level': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {'editable': 'False'}),
            'parent': ('models.ForeignKey', ["orm['cms.CMSPlugin']"], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'placeholder': ('models.CharField', ['_("slot")'], {'max_length': '50', 'editable': 'False', 'db_index': 'True'}),
            'plugin_type': ('models.CharField', ['_("plugin_name")'], {'max_length': '50', 'editable': 'False', 'db_index': 'True'}),
            'position': ('models.PositiveSmallIntegerField', ['_("position")'], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'tree_id': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'})
        },
        'cms.pagemoderator': {
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'moderate_children': ('models.BooleanField', ["_('Moderate children')"], {'blank': 'True'}),
            'moderate_descendants': ('models.BooleanField', ["_('Moderate descendants')"], {'blank': 'True'}),
            'moderate_page': ('models.BooleanField', ["_('Moderate page')"], {'blank': 'True'}),
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label','codename')", 'unique_together': "(('content_type','codename'),)"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.title': {
            'Meta': {'unique_together': "('language','page')"},
            'application_urls': ('models.CharField', ["_('application')"], {'blank': 'True', 'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'creation_date': ('models.DateTimeField', ['_("creation date")'], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'has_url_overwrite': ('models.BooleanField', ['_("has url overwrite")'], {'default': 'False', 'editable': 'False', 'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', ['_("language")'], {'max_length': '5', 'db_index': 'True'}),
            'menu_title': ('models.CharField', ['_("title")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('models.TextField', ['_("description")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('models.CharField', ['_("keywords")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {'related_name': '"title_set"'}),
            'page_title': ('models.CharField', ['_("title")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('models.CharField', ['_("path")'], {'max_length': '255', 'db_index': 'True'}),
            'public': '<< PUT FIELD DEFINITION HERE >>',
            'redirect': ('models.CharField', ['_("redirect")'], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('models.SlugField', ['_("slug")'], {'unique': 'False', 'max_length': '255', 'db_index': 'True'}),
            'title': ('models.CharField', ['_("title")'], {'max_length': '255'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            'author': ('models.ForeignKey', ["orm['auth.User']"], {'limit_choices_to': "{'page__isnull':False}"}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime.now', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('models.BooleanField', ['_("in navigation")'], {'default': 'True', 'db_index': 'True'}),
            'level': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'lft': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'login_required': ('models.BooleanField', ["_('login required')"], {'default': 'False'}),
            'moderator_state': ('models.SmallIntegerField', ["_('moderator state')"], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('models.CharField', ['_("navigation extenders")'], {'blank': 'True', 'max_length': '80', 'null': 'True', 'db_index': 'True'}),
            'parent': ('models.ForeignKey', ["orm['cms.Page']"], {'db_index': 'True', 'related_name': "'children'", 'null': 'True', 'blank': 'True'}),
            'public': '<< PUT FIELD DEFINITION HERE >>',
            'publication_date': ('models.DateTimeField', ['_("publication date")'], {'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'publication_end_date': ('models.DateTimeField', ['_("publication end date")'], {'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'published': ('models.BooleanField', ['_("is published")'], {'blank': 'True'}),
            'reverse_id': ('models.CharField', ['_("id")'], {'blank': 'True', 'max_length': '40', 'null': 'True', 'db_index': 'True'}),
            'rght': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'}),
            'sites': ('models.ManyToManyField', ["orm['sites.Site']"], {}),
            'soft_root': ('models.BooleanField', ['_("soft root")'], {'default': 'False', 'db_index': 'True'}),
            'template': ('models.CharField', ['_("template")'], {'max_length': '100'}),
            'tree_id': ('models.PositiveIntegerField', [], {'editable': 'False', 'db_index': 'True'})
        },
        'cms.pagemoderatorstate': {
            'Meta': {'ordering': "('page','action','-created')"},
            'action': ('models.CharField', [], {'blank': 'True', 'max_length': '3', 'null': 'True'}),
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'message': ('models.TextField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'page': ('models.ForeignKey', ["orm['cms.Page']"], {}),
            'user': ('models.ForeignKey', ["orm['auth.User']"], {'null': 'True'})
        },
        'auth.group': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'cms.pageusergroup': {
            'Meta': {'_bases': ['django.contrib.auth.models.Group']},
            'created_by': ('models.ForeignKey', ["orm['auth.User']"], {'related_name': '"created_usergroups"'}),
            'group_ptr': ('models.OneToOneField', ["orm['auth.Group']"], {})
        }
    }
    
    complete_apps = ['cms']
