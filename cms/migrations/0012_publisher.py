
from south.db import db
from django.db import models
from cms.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'PublicCMSPlugin'
        db.create_table('cms_publiccmsplugin', (
            ('rght', orm['cms.publiccmsplugin:rght']),
            ('parent', orm['cms.publiccmsplugin:parent']),
            ('language', orm['cms.publiccmsplugin:language']),
            ('level', orm['cms.publiccmsplugin:level']),
            ('mark_delete', orm['cms.publiccmsplugin:mark_delete']),
            ('page', orm['cms.publiccmsplugin:page']),
            ('lft', orm['cms.publiccmsplugin:lft']),
            ('tree_id', orm['cms.publiccmsplugin:tree_id']),
            ('position', orm['cms.publiccmsplugin:position']),
            ('creation_date', orm['cms.publiccmsplugin:creation_date']),
            ('placeholder', orm['cms.publiccmsplugin:placeholder']),
            ('id', orm['cms.publiccmsplugin:id']),
            ('plugin_type', orm['cms.publiccmsplugin:plugin_type']),
        ))
        db.send_create_signal('cms', ['PublicCMSPlugin'])
        
        # Adding model 'PageUser'
        db.create_table('cms_pageuser', (
            ('user_ptr', orm['cms.pageuser:user_ptr']),
            ('created_by', orm['cms.pageuser:created_by']),
        ))
        db.send_create_signal('cms', ['PageUser'])
        
        # Adding model 'PublicTitle'
        db.create_table('cms_publictitle', (
            ('menu_title', orm['cms.publictitle:menu_title']),
            ('redirect', orm['cms.publictitle:redirect']),
            ('meta_keywords', orm['cms.publictitle:meta_keywords']),
            ('page_title', orm['cms.publictitle:page_title']),
            ('language', orm['cms.publictitle:language']),
            ('title', orm['cms.publictitle:title']),
            ('has_url_overwrite', orm['cms.publictitle:has_url_overwrite']),
            ('application_urls', orm['cms.publictitle:application_urls']),
            ('creation_date', orm['cms.publictitle:creation_date']),
            ('id', orm['cms.publictitle:id']),
            ('path', orm['cms.publictitle:path']),
            ('meta_description', orm['cms.publictitle:meta_description']),
            ('slug', orm['cms.publictitle:slug']),
            ('mark_delete', orm['cms.publictitle:mark_delete']),
            ('page', orm['cms.publictitle:page']),
        ))
        db.send_create_signal('cms', ['PublicTitle'])
        
        # Adding model 'GlobalPagePermission'
        db.create_table('cms_globalpagepermission', (
            ('can_publish', orm['cms.globalpagepermission:can_publish']),
            ('group', orm['cms.globalpagepermission:group']),
            ('can_moderate', orm['cms.globalpagepermission:can_moderate']),
            ('can_change', orm['cms.globalpagepermission:can_change']),
            ('can_change_permissions', orm['cms.globalpagepermission:can_change_permissions']),
            ('can_recover_page', orm['cms.globalpagepermission:can_recover_page']),
            ('can_add', orm['cms.globalpagepermission:can_add']),
            ('user', orm['cms.globalpagepermission:user']),
            ('can_delete', orm['cms.globalpagepermission:can_delete']),
            ('can_move_page', orm['cms.globalpagepermission:can_move_page']),
            ('id', orm['cms.globalpagepermission:id']),
            ('can_change_softroot', orm['cms.globalpagepermission:can_change_softroot']),
        ))
        db.send_create_signal('cms', ['GlobalPagePermission'])
        
        # Adding model 'PublicPage'
        db.create_table('cms_publicpage', (
            ('rght', orm['cms.publicpage:rght']),
            ('level', orm['cms.publicpage:level']),
            ('navigation_extenders', orm['cms.publicpage:navigation_extenders']),
            ('parent', orm['cms.publicpage:parent']),
            ('author', orm['cms.publicpage:author']),
            ('reverse_id', orm['cms.publicpage:reverse_id']),
            ('login_required', orm['cms.publicpage:login_required']),
            ('mark_delete', orm['cms.publicpage:mark_delete']),
            ('site', orm['cms.publicpage:site']),
            ('soft_root', orm['cms.publicpage:soft_root']),
            ('creation_date', orm['cms.publicpage:creation_date']),
            ('lft', orm['cms.publicpage:lft']),
            ('publication_end_date', orm['cms.publicpage:publication_end_date']),
            ('moderator_state', orm['cms.publicpage:moderator_state']),
            ('template', orm['cms.publicpage:template']),
            ('published', orm['cms.publicpage:published']),
            ('tree_id', orm['cms.publicpage:tree_id']),
            ('publication_date', orm['cms.publicpage:publication_date']),
            ('in_navigation', orm['cms.publicpage:in_navigation']),
            ('id', orm['cms.publicpage:id']),
        ))
        db.send_create_signal('cms', ['PublicPage'])
        
        # Adding model 'PageModerator'
        db.create_table('cms_pagemoderator', (
            ('moderate_page', orm['cms.pagemoderator:moderate_page']),
            ('moderate_children', orm['cms.pagemoderator:moderate_children']),
            ('page', orm['cms.pagemoderator:page']),
            ('user', orm['cms.pagemoderator:user']),
            ('id', orm['cms.pagemoderator:id']),
            ('moderate_descendants', orm['cms.pagemoderator:moderate_descendants']),
        ))
        db.send_create_signal('cms', ['PageModerator'])
        
        # Adding model 'PageModeratorState'
        db.create_table('cms_pagemoderatorstate', (
            ('created', orm['cms.pagemoderatorstate:created']),
            ('page', orm['cms.pagemoderatorstate:page']),
            ('user', orm['cms.pagemoderatorstate:user']),
            ('action', orm['cms.pagemoderatorstate:action']),
            ('message', orm['cms.pagemoderatorstate:message']),
            ('id', orm['cms.pagemoderatorstate:id']),
        ))
        db.send_create_signal('cms', ['PageModeratorState'])
        
        # Adding model 'PageUserGroup'
        db.create_table('cms_pageusergroup', (
            ('group_ptr', orm['cms.pageusergroup:group_ptr']),
            ('created_by', orm['cms.pageusergroup:created_by']),
        ))
        db.send_create_signal('cms', ['PageUserGroup'])
        
        # Adding field 'PagePermission.can_delete'
        db.add_column('cms_pagepermission', 'can_delete', orm['cms.pagepermission:can_delete'])
        
        # Adding field 'Page.moderator_state'
        db.add_column('cms_page', 'moderator_state', orm['cms.page:moderator_state'])
        
        # Adding field 'Page.published'
        db.add_column('cms_page', 'published', orm['cms.page:published'])
        
        # Adding field 'Page.site'
        db.add_column('cms_page', 'site', orm['cms.page:site'])
        
        # Adding field 'CMSPlugin.inherited_public'
        db.add_column('cms_cmsplugin', 'inherited_public', orm['cms.cmsplugin:inherited_public'])
        
        # Adding field 'PagePermission.can_change_permissions'
        db.add_column('cms_pagepermission', 'can_change_permissions', orm['cms.pagepermission:can_change_permissions'])
        
        # Adding field 'PagePermission.can_moderate'
        db.add_column('cms_pagepermission', 'can_moderate', orm['cms.pagepermission:can_moderate'])
        
        # Adding field 'PagePermission.can_add'
        db.add_column('cms_pagepermission', 'can_add', orm['cms.pagepermission:can_add'])
        
        # Adding field 'Page.public'
        db.add_column('cms_page', 'public', orm['cms.page:public'])
        
        # Adding field 'PagePermission.grant_on'
        db.add_column('cms_pagepermission', 'grant_on', orm['cms.pagepermission:grant_on'])
        
        # Adding field 'PagePermission.can_move_page'
        db.add_column('cms_pagepermission', 'can_move_page', orm['cms.pagepermission:can_move_page'])
        
        # Adding field 'Title.public'
        db.add_column('cms_title', 'public', orm['cms.title:public'])
        
        # Adding field 'PagePermission.can_change'
        db.add_column('cms_pagepermission', 'can_change', orm['cms.pagepermission:can_change'])
        
        # Deleting field 'PagePermission.everybody'
        db.delete_column('cms_pagepermission', 'everybody')
        
        # Deleting field 'PagePermission.type'
        db.delete_column('cms_pagepermission', 'type')
        
        # Deleting field 'Page.status'
        db.delete_column('cms_page', 'status')
        
        # Dropping ManyToManyField 'Page.sites'
        db.delete_table('cms_page_sites')
        
        # Deleting field 'PagePermission.can_edit'
        db.delete_column('cms_pagepermission', 'can_edit')
        
        # Creating unique_together for [language, page] on PublicTitle.
        db.create_unique('cms_publictitle', ['language', 'page_id'])
        
        if not db.dry_run:
            pages = orm.Page.objects.all()
            for page in pages:
                page.site_id = 1
                page.save()
                
            
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
        
        # Deleting field 'Page.site'
        db.delete_column('cms_page', 'site_id')
        
        # Deleting field 'CMSPlugin.inherited_public'
        db.delete_column('cms_cmsplugin', 'inherited_public_id')
        
        # Deleting field 'PagePermission.can_change_permissions'
        db.delete_column('cms_pagepermission', 'can_change_permissions')
        
        # Deleting field 'PagePermission.can_moderate'
        db.delete_column('cms_pagepermission', 'can_moderate')
        
        # Deleting field 'PagePermission.can_add'
        db.delete_column('cms_pagepermission', 'can_add')
        
        # Deleting field 'Page.public'
        db.delete_column('cms_page', 'public_id')
        
        # Deleting field 'PagePermission.grant_on'
        db.delete_column('cms_pagepermission', 'grant_on')
        
        # Deleting field 'PagePermission.can_move_page'
        db.delete_column('cms_pagepermission', 'can_move_page')
        
        # Deleting field 'Title.public'
        db.delete_column('cms_title', 'public_id')
        
        # Deleting field 'PagePermission.can_change'
        db.delete_column('cms_pagepermission', 'can_change')
        
        # Adding field 'PagePermission.everybody'
        db.add_column('cms_pagepermission', 'everybody', orm['cms.pagepermission:everybody'])
        
        # Adding field 'PagePermission.type'
        db.add_column('cms_pagepermission', 'type', orm['cms.pagepermission:type'])
        
        # Adding field 'Page.status'
        db.add_column('cms_page', 'status', orm['cms.page:status'])
        
        # Adding ManyToManyField 'Page.sites'
        db.create_table('cms_page_sites', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm.Page, null=False)),
            ('site', models.ForeignKey(orm['sites.site'], null=False))
        ))
        
        # Adding field 'PagePermission.can_edit'
        db.add_column('cms_pagepermission', 'can_edit', orm['cms.pagepermission:can_edit'])
        
        # Deleting unique_together for [language, page] on PublicTitle.
        db.delete_unique('cms_publictitle', ['language', 'page_id'])
        
    
    
    models = {
        'cms.publiccmsplugin': {
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 15, 178714)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.PublicPage']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.PublicCMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pageuser': {
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_users'", 'to': "orm['auth.User']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'db_table': "'django_site'"},
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 17, 165429)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 17, 165256)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'cms.publictitle': {
            'Meta': {'unique_together': "(('language', 'page'),)"},
            'application_urls': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 15, 525211)'}),
            'has_url_overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'menu_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'title_set'", 'to': "orm['cms.PublicPage']"}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'redirect': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms.globalpagepermission': {
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_change_softroot': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_recover_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'cms.publicpage': {
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 16, 369082)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'mark_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.PublicPage']"}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagepermission': {
            'can_add': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_change_permissions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_change_softroot': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_delete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_moderate': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_move_page': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'grant_on': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'cms.title': {
            'Meta': {'unique_together': "(('language', 'page'),)"},
            'application_urls': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 18, 38897)'}),
            'has_url_overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'menu_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'title_set'", 'to': "orm['cms.Page']"}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PublicTitle']"}),
            'redirect': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'cms.cmsplugin': {
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 18, 483591)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'inherited_public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'inherited_origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PublicCMSPlugin']"}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.page': {
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 6, 29, 9, 2, 17, 642856)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'public': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'origin'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.PublicPage']"}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.pagemoderatorstate': {
            'action': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'cms.pagemoderator': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'moderate_children': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderate_descendants': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'moderate_page': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'cms.pageusergroup': {
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_usergroups'", 'to': "orm['auth.User']"}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['cms']
