'''
Created on Dec 10, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''


from __future__ import with_statement
from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission
from cms.tests import base
from cms.tests.base import CMSTestCase
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site

class AdminTestCase(CMSTestCase):
    
    def _get_guys(self):
        admin = User(username="admin", is_staff = True, is_active = True, is_superuser = True)
        admin.set_password("admin")
        admin.save()
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