'''
Created on Dec 10, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''


from __future__ import with_statement
from cms.models.pagemodel import Page
from cms.tests import base
from cms.tests.base import CMSTestCase
from cms.tests.util.settings_contextmanager import SettingsOverride
from django.conf import settings
from django.contrib.auth.models import User

class AdminTestCase(CMSTestCase):
    
    def _get_guys(self):
        admin = User(username="admin", is_staff = True, is_active = True, is_superuser = True)
        admin.set_password("admin")
        admin.save()
        self.login_user(admin)
        USERNAME = 'test'
        data = {
            'username': USERNAME, 
            'password1': USERNAME,
            'password2': USERNAME, 
            'can_add_page': True, 
            'can_change_page': True, 
            'can_delete_page': True, 
            'can_recover_page': True, 
            'can_add_pageuser': False, 
            'can_change_pageuser': False, 
            'can_delete_pageuser': False, 
            'can_add_pagepermission': False, 
            'can_change_pagepermission': False, 
            'can_delete_pagepermission': False,
        }
        response = self.client.post('/admin/cms/pageuser/add/', data)
        self.assertRedirects(response, '/admin/cms/pageuser/')
        
        normal_guy = User.objects.get(username=USERNAME)
        normal_guy.is_staff = True
        normal_guy.is_active = True
        normal_guy.save()
        return admin, normal_guy
    
    def test_01_edit_does_not_reset_page_adv_fields(self):
        
        NEW_PAGE_NAME = 'Test page 2'
        REVERSE_ID = 'Test'
        
        admin, normal_guy = self._get_guys()
        
        # The admin creates the page
        page = self.create_page(None, admin, 1, 'Test Page')
        page.reverse_id = REVERSE_ID
        page.save()
        
        # The user edits the page (change the page name for ex.)
        page_data = {
            'title':NEW_PAGE_NAME, 
            'slug':page.get_slug(), 
            'language':settings.LANGUAGES[0][0],
            'site':page.site.pk, 
            'template':page.template
        }
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        
        self.login_user(normal_guy)
        with SettingsOverride(CMS_PERMISSION=False):
            resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data, 
                                    follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateNotUsed(resp, 'admin/login.html')
        page = Page.objects.get(pk=page.pk)
        
        self.assertEqual(page.get_title(), NEW_PAGE_NAME)
        self.assertEqual(page.reverse_id, REVERSE_ID)