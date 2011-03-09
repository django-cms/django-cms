# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.admin.dialog.forms import (ModeratorForm, PermissionForm, 
    PermissionAndModeratorForm)
from cms.admin.dialog.views import _form_class_selector
from cms.api import create_page, create_title
from cms.models.pagemodel import Page
from cms.test_utils import testcases as base
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE_DELETE, 
    URL_CMS_PAGE, URL_CMS_TRANSLATION_DELETE)
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

class AdminTestCase(CMSTestCase):
    fixtures = ['admin_guys.json']
    
    def _get_guys(self, admin_only=False):
        admin = User.objects.get(username="admin")
        if admin_only:
            return admin
        normal_guy = User.objects.get(username="test")
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
