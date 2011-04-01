# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.admin.dialog.forms import (ModeratorForm, PermissionForm, 
    PermissionAndModeratorForm)
from cms.admin.dialog.views import _form_class_selector
from cms.admin.pageadmin import contribute_fieldsets, contribute_list_filter
from cms.api import create_page, create_title
from cms.apphook_pool import apphook_pool, ApphookPool
from cms.models.moderatormodels import PageModeratorState
from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission
from cms.test_utils import testcases as base
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE_DELETE, 
    URL_CMS_PAGE, URL_CMS_TRANSLATION_DELETE)
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.sites import site
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404
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
        
        site = Site.objects.get(pk=1)
    
        # The admin creates the page
        page = create_page(OLD_PAGE_NAME, "nav_playground.html", "en",
                           site=site, created_by=admin)
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
        page_data['pagepermission_set-2-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-2-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-2-MAX_NUM_FORMS'] = 0
        
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
        page_data['pagepermission_set-2-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-2-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-2-MAX_NUM_FORMS'] = 0
        
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
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin, published=True)
        child = create_page('child-page', "nav_playground.html", "en",
                            created_by=admin, published=True, parent=page)
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
        page = create_page("delete-page-translation", "nav_playground.html", "en",
                           created_by=admin, published=True)
        create_title("de", "delete-page-translation-2", page, slug="delete-page-translation-2")
        self.login_user(admin)
        response = self.client.get(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})
        self.assertEqual(response.status_code, 200)
        response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})
        self.assertRedirects(response, URL_CMS_PAGE)
    
    def test_08_change_template(self):
        request = self.get_request('/admin/cms/page/1/', 'en')
        pageadmin = site._registry[Page]
        self.assertRaises(Http404, pageadmin.change_template, request, 1)
        page = create_page('test-page', 'nav_playground.html', 'en')
        response = pageadmin.change_template(request, page.pk)
        self.assertEqual(response.status_code, 403)
        admin = self._get_guys(True)
        url = reverse('admin:cms_page_change_template', args=(page.pk,))
        with self.login_user_context(admin):
            response = self.client.post(url, {'template': 'doesntexist'})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content, "template not valid")
            response = self.client.post(url, {'template': settings.CMS_TEMPLATES[0][0]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, 'ok')
            
    def test_09_get_permissions(self):
        page = create_page('test-page', 'nav_playground.html', 'en')
        url = reverse('admin:cms_page_get_permissions', args=(page.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/login.html')
        admin = self._get_guys(True)
        with self.login_user_context(admin):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateNotUsed(response, 'admin/login.html')


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


class AdminTests(CMSTestCase):
    # TODO: needs tests for actual permissions, not only superuser/normaluser
    
    def setUp(self):
        create_page("testpage", "nav_playground.html", "en")
    
    @property
    def admin_class(self):
        return admin.site._registry[Page]
    
    def get_admin(self):
        usr = User(username="admin", email="admin@django-cms.org", is_staff=True, is_superuser=True)
        usr.set_password("admin")
        usr.save()
        return usr
    
    def get_staff(self):
        usr = User(username="test", email="test@django-cms.org", is_staff=True)
        usr.set_password("test")
        usr.save()
        return usr
    
    def get_permless(self):
        usr = User(username="permless", email="permless@django-cms.org")
        usr.set_password("permless")
        usr.save()
        return usr
    
    def get_page(self):
        return Page.objects.get(pk=1)
    
    def test_get_moderation_state_requires_perms(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            self.assertRaises(Http404, self.admin_class.get_moderation_states,
                              request, 1)
    
    def test_get_moderation_state(self):
        with self.login_user_context(self.get_admin()):
            request = self.get_request()
            response = self.admin_class.get_moderation_states(request, 1)
            self.assertEqual(response.status_code, 200)
            
    def test_remove_delete_state_requires_perms(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            self.assertRaises(PermissionDenied, self.admin_class.remove_delete_state,
                              request, 1)
            
    def test_remove_delete_states(self):
        page = self.get_page()
        admin = self.get_admin()
        PageModeratorState.objects.create(page=page, user=admin, action="DEL")
        with self.login_user_context(admin):
            self.assertEqual(page.pagemoderatorstate_set.get_delete_actions().count(), 1)
            request = self.get_request()
            response = self.admin_class.remove_delete_state(request, 1)
            self.assertEqual(response.status_code, 302)
            page = self.reload(page)
            self.assertEqual(page.pagemoderatorstate_set.get_delete_actions().count(), 0)
    
    def test_change_status_requires_post(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            response = self.admin_class.change_status(request, 1)
            self.assertEqual(response.status_code, 405)
    
    def test_change_status_requires_perms(self):
        with self.login_user_context(self.get_permless()):
            url = reverse('admin:cms_page_change_status', args=(1,))
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, 403)
    
    def test_change_innavigation_requires_post(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            response = self.admin_class.change_innavigation(request, 1)
            self.assertEqual(response.status_code, 405)

    def test_change_moderation_requires_post(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            response = self.admin_class.change_moderation(request, 1)
            self.assertEqual(response.status_code, 405)

    def test_approve_page_requires_perms(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            self.assertRaises(Http404, self.admin_class.approve_page,
                              request, 1)

    def test_publish_page_requires_perms(self):
        with self.login_user_context(self.get_permless()):
            request = self.get_request()
            response = self.admin_class.publish_page(request, 1)
            self.assertEqual(response.status_code, 403)
