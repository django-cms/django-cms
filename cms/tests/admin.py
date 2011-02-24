# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.admin.dialog.forms import (ModeratorForm, PermissionForm, 
    PermissionAndModeratorForm)
from cms.admin.dialog.views import _form_class_selector
from cms.admin.pageadmin import contribute_fieldsets, contribute_list_filter
from cms.apphook_pool import apphook_pool, ApphookPool
from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission
from cms.test_utils import testcases as base
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE_DELETE, 
    URL_CMS_PAGE, URL_CMS_TRANSLATION_DELETE)
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from menus.menu_pool import menu_pool
from types import MethodType
from unittest import TestCase


class AdminTestCase(CMSTestCase):
    
    def _get_guys(self, admin_only=False):
        admin = self.get_superuser()
        if admin_only:
            return admin
        self.login_user(admin)
        USERNAME = 'test'
        
        normal_guy = User.objects.create_user(USERNAME, 'test@test.com', USERNAME)
        normal_guy.is_staff = True
        normal_guy.is_active = True
        normal_guy.save()
        normal_guy.user_permissions = Permission.objects.filter(
            codename__in=['change_page', 'change_title', 'add_page', 'add_title', 'delete_page', 'delete_title']
        )
        gpp = GlobalPagePermission.objects.create(
            user=normal_guy,
            can_change=True,
            can_delete=True,
            can_change_advanced_settings=False,
            can_publish=True,
            can_change_permissions=False,
            can_move_page=True,
            can_moderate=True,
        )
        gpp.sites = Site.objects.all()
        return admin, normal_guy
    
    def test_01_edit_does_not_reset_page_adv_fields(self):
        """
        Makes sure that if a non-superuser with no rights to edit advanced page
        fields edits a page, those advanced fields are not touched.
        """
        OLD_PAGE_NAME = 'Test Page'
        NEW_PAGE_NAME = 'Test page 2'
        REVERSE_ID = 'Test'
        OVERRIDE_URL = 'my/override/url'
        
        admin, normal_guy = self._get_guys()
        
        # The admin creates the page
        page = self.create_page(None, admin, 1, OLD_PAGE_NAME)
        page.reverse_id = REVERSE_ID
        page.save()
        title = page.get_title_obj()
        title.has_url_overwrite = True
        title.path = OVERRIDE_URL
        title.save()
        
        self.assertEqual(page.get_title(), OLD_PAGE_NAME)
        self.assertEqual(page.reverse_id, REVERSE_ID)
        self.assertEqual(title.overwrite_url, OVERRIDE_URL)
        
        # The user edits the page (change the page name for ex.)
        page_data = {
            'title': NEW_PAGE_NAME, 
            'slug': page.get_slug(), 
            'language': title.language,
            'site': page.site.pk, 
            'template': page.template,
        }
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        
        self.login_user(normal_guy)
        resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data, 
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateNotUsed(resp, 'admin/login.html')
        page = Page.objects.get(pk=page.pk)
        
        self.assertEqual(page.get_title(), NEW_PAGE_NAME)
        self.assertEqual(page.reverse_id, REVERSE_ID)
        title = page.get_title_obj()
        self.assertEqual(title.overwrite_url, OVERRIDE_URL)
        
        # The admin edits the page (change the page name for ex.)
        page_data = {
            'title': OLD_PAGE_NAME, 
            'slug': page.get_slug(), 
            'language': title.language,
            'site': page.site.pk, 
            'template': page.template,
            'reverse_id': page.reverse_id,
        }
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        
        self.login_user(admin)
        resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data, 
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateNotUsed(resp, 'admin/login.html')
        page = Page.objects.get(pk=page.pk)
        
        self.assertEqual(page.get_title(), OLD_PAGE_NAME)
        self.assertEqual(page.reverse_id, REVERSE_ID)
        title = page.get_title_obj()
        self.assertEqual(title.overwrite_url, None)

    def test_02_delete(self):
        admin = self._get_guys(True)
        page = self.create_page(user=admin, title="delete-page", published=True)
        child = self.create_page(page, user=admin, title="delete-page", published=True)
        self.login_user(admin)
        data = {'post': 'yes'}
        response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)
        self.assertRedirects(response, URL_CMS_PAGE)
        self.assertRaises(Page.DoesNotExist, self.reload, page)
        self.assertRaises(Page.DoesNotExist, self.reload, child)
        
    def test_03_admin_dialog_form_no_moderation_or_permissions(self):
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            result = _form_class_selector()
            self.assertEqual(result, None)
            
    def test_04_admin_dialog_form_permission_only(self):
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=True):
            result = _form_class_selector()
            self.assertEqual(result, PermissionForm)
            
    def test_05_admin_dialog_form_moderation_only(self):
        with SettingsOverride(CMS_MODERATOR=True, CMS_PERMISSION=False):
            result = _form_class_selector()
            self.assertEqual(result, ModeratorForm)
            
    def test_05_admin_dialog_form_moderation_and_permisison(self):
        with SettingsOverride(CMS_MODERATOR=True, CMS_PERMISSION=True):
            result = _form_class_selector()
            self.assertEqual(result, PermissionAndModeratorForm)

    def test_06_search_fields(self):
        superuser = self._get_guys(admin_only=True)
        from django.contrib.admin import site
        with self.login_user_context(superuser):
            for model, admin in site._registry.items():
                if model._meta.app_label != 'cms':
                    continue
                if not admin.search_fields:
                    continue
                url = reverse('admin:cms_%s_changelist' % model._meta.module_name)
                response = self.client.get('%s?q=1' % url)
                errmsg = response.content
                self.assertEqual(response.status_code, 200, errmsg)

    def test_07_delete_translation(self):
        admin = self._get_guys(True)
        page = self.create_page(user=admin, title="delete-page-ranslation", published=True)
        title = self.create_title("delete-page-ranslation-2", "delete-page-ranslation-2", 'nb', page)
        self.login_user(admin)
        response = self.client.get(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'nb'})
        self.assertEqual(response.status_code, 200)
        response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'nb'})
        self.assertRedirects(response, URL_CMS_PAGE)


class AdminFieldsetTests(TestCase):
    def validate_attributes(self, a, b, ignore=None):
        attrs = ['advanced_fields', 'hidden_fields', 'general_fields',
                 'template_fields', 'additional_hidden_fields', 'fieldsets']
        if not ignore:
            ignore = []
        for attr in attrs:
            if attr in ignore:
                continue
            a_attr = getattr(a, attr)
            b_attr = getattr(b, attr)
            self.assertEqual(a_attr, b_attr)
        
    def test_no_moderator(self):
        with SettingsOverride(CMS_MODERATOR=True):
            control = AttributeObject()
            contribute_fieldsets(control)
        with SettingsOverride(CMS_MODERATOR=False):
            nomod = AttributeObject()
            contribute_fieldsets(nomod)
        self.validate_attributes(control, nomod, ['fieldsets', 'additional_hidden_fields'])
        self.assertEqual(control.additional_hidden_fields, ['moderator_state', 'moderator_message'])
        self.assertEqual(nomod.additional_hidden_fields, [])
    
    def test_no_menu_title_overwrite(self):
        with SettingsOverride(CMS_MENU_TITLE_OVERWRITE=True):
            control = AttributeObject()
            contribute_fieldsets(control)
        with SettingsOverride(CMS_MENU_TITLE_OVERWRITE=False):
            experiment = AttributeObject()
            contribute_fieldsets(experiment)
        self.validate_attributes(control, experiment, ['fieldsets', 'general_fields'])
        self.assertEqual(control.general_fields[0], ('title', 'menu_title'))
        self.assertEqual(experiment.general_fields[0], 'title')
    
    def test_no_softroot(self):
        with SettingsOverride(CMS_SOFTROOT=True):
            control = AttributeObject()
            contribute_fieldsets(control)
        with SettingsOverride(CMS_SOFTROOT=False):
            experiment = AttributeObject()
            contribute_fieldsets(experiment)
        self.validate_attributes(control, experiment, ['fieldsets', 'advanced_fields'])
        self.assertTrue('soft_root' in control.advanced_fields)
        self.assertFalse('soft_root' in experiment.advanced_fields)
    
    def test_dates(self):
        with SettingsOverride(CMS_SHOW_START_DATE=False, CMS_SHOW_END_DATE=False):
            control = AttributeObject()
        contribute_fieldsets(control)
        with SettingsOverride(CMS_SHOW_START_DATE=True, CMS_SHOW_END_DATE=True):
            experiment1 = AttributeObject()
            contribute_fieldsets(experiment1)
        with SettingsOverride(CMS_SHOW_START_DATE=True, CMS_SHOW_END_DATE=False):
            experiment2 = AttributeObject()
            contribute_fieldsets(experiment2)
        with SettingsOverride(CMS_SHOW_START_DATE=False, CMS_SHOW_END_DATE=True):
            experiment3 = AttributeObject()
            contribute_fieldsets(experiment3)
        self.validate_attributes(control, experiment1, ['fieldsets', 'general_fields'])
        self.validate_attributes(control, experiment2, ['fieldsets', 'general_fields'])
        self.validate_attributes(control, experiment3, ['fieldsets', 'general_fields'])
        self.assertFalse(('publication_date', 'publication_end_date') in control.general_fields, control.general_fields)
        self.assertTrue(('publication_date', 'publication_end_date') in experiment1.general_fields, experiment1.general_fields)
        self.assertFalse(('publication_date', 'publication_end_date') in experiment2.general_fields, experiment2.general_fields)
        self.assertFalse(('publication_date', 'publication_end_date') in experiment3.general_fields, experiment3.general_fields)
        self.assertFalse('publication_end_date' in experiment1.general_fields, experiment1.general_fields)
        self.assertFalse('publication_end_date' in experiment2.general_fields, experiment2.general_fields)
        self.assertTrue('publication_end_date' in experiment3.general_fields, experiment3.general_fields)
        self.assertFalse('publication_date' in experiment1.general_fields, experiment1.general_fields)
        self.assertTrue('publication_date' in experiment2.general_fields, experiment2.general_fields)
        self.assertFalse('publication_date' in experiment3.general_fields, experiment3.general_fields)
    
    def test_no_seo(self):
        with SettingsOverride(CMS_SEO_FIELDS=True):
            control = AttributeObject()
            contribute_fieldsets(control)
        with SettingsOverride(CMS_SEO_FIELDS=False):
            experiment = AttributeObject()
            contribute_fieldsets(experiment)
        self.validate_attributes(control, experiment, ['fieldsets', 'seo_fields'])
        self.assertEqual(control.seo_fields, ['page_title', 'meta_description', 'meta_keywords'])
        self.assertFalse(experiment.seo_fields, [])
    
    def test_url_overwrite(self):
        with SettingsOverride(CMS_URL_OVERWRITE=False):
            control = AttributeObject()
            contribute_fieldsets(control)
        with SettingsOverride(CMS_URL_OVERWRITE=True):
            experiment = AttributeObject()
            contribute_fieldsets(experiment)
        self.validate_attributes(control, experiment, ['fieldsets', 'advanced_fields'])
        self.assertFalse('overwrite_url' in control.advanced_fields, control.advanced_fields)
        self.assertTrue('overwrite_url' in experiment.advanced_fields, experiment.advanced_fields)
        
    def test_no_cms_enabled_menus(self):
        control = AttributeObject()
        contribute_fieldsets(control)
        old_menus = menu_pool.menus.copy()
        menu_pool.menus = {}
        experiment = AttributeObject()
        contribute_fieldsets(experiment)
        menu_pool.menus = old_menus
        self.validate_attributes(control, experiment, ['fieldsets', 'advanced_fields'])
        self.assertTrue('navigation_extenders' in control.advanced_fields, control.advanced_fields)
        self.assertFalse('navigation_extenders' in experiment.advanced_fields, experiment.advanced_fields)
        
    def test_redirects(self):
        with SettingsOverride(CMS_REDIRECTS=False):
            control = AttributeObject()
            contribute_fieldsets(control)
        with SettingsOverride(CMS_REDIRECTS=True):
            experiment = AttributeObject()
            contribute_fieldsets(experiment)
        self.validate_attributes(control, experiment, ['fieldsets', 'advanced_fields'])
        self.assertFalse('redirect' in control.advanced_fields, control.advanced_fields)
        self.assertTrue('redirect' in experiment.advanced_fields, experiment.advanced_fields)
        
        
    def test_no_apphooks(self):
        def func_true(self):
            return True
        def func_false(self):
            return False
        apphook_pool.get_apphooks = MethodType(func_true, apphook_pool, ApphookPool)
        control = AttributeObject()
        contribute_fieldsets(control)
        apphook_pool.get_apphooks = MethodType(func_false, apphook_pool, ApphookPool)
        experiment = AttributeObject()
        contribute_fieldsets(experiment)
        self.validate_attributes(control, experiment, ['fieldsets', 'advanced_fields'])
        self.assertTrue('application_urls' in control.advanced_fields, control.advanced_fields)
        self.assertFalse('application_urls' in experiment.advanced_fields, control.advanced_fields)
        

class AdminListFilterTests(TestCase):
    def test_no_moderator(self):
        with SettingsOverride(CMS_MODERATOR=True):
            control = AttributeObject()
            contribute_list_filter(control)
        with SettingsOverride(CMS_MODERATOR=False):
            experiment = AttributeObject()
            contribute_list_filter(experiment)
        self.assertTrue('moderator_state' in control.list_filter, control.list_filter)
        self.assertFalse('moderator_state' in experiment.list_filter, experiment.list_filter)
    
    def test_no_softroot(self):
        with SettingsOverride(CMS_SOFTROOT=True):
            control = AttributeObject()
            contribute_list_filter(control)
        with SettingsOverride(CMS_SOFTROOT=False):
            experiment = AttributeObject()
            contribute_list_filter(experiment)
        self.assertTrue('soft_root' in control.list_filter, control.list_filter)
        self.assertFalse('soft_root' in experiment.list_filter, experiment.list_filter)