'''
Created on Jan 4, 2011

@author: Christopher Glass <christopher.glass@divio.ch>
'''
from __future__ import with_statement
from cms.forms.utils import get_site_choices, get_page_choices
from cms.tests.base import CMSTestCase
from cms.tests.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.core.cache import cache

class FormsTestCase(CMSTestCase):
    def setUp(self):
        cache.clear()
        
    def test_01_get_site_choices(self):
        result = get_site_choices()
        self.assertEquals(result, [])
        
    def test_02_get_page_choices(self):
        result = get_page_choices()
        self.assertEquals(result, [('', '----')])
        
    def test_03_get_site_choices_without_moderator(self):
        with SettingsOverride(CMS_MODERATOR=False):
            result = get_site_choices()
            self.assertEquals(result, [])
            
    def test_04_get_site_choices_without_moderator(self):
        with SettingsOverride(CMS_MODERATOR=False):
            # boilerplate (creating a page)
            user_super = User(username="super", is_staff=True, is_active=True, 
                is_superuser=True)
            user_super.set_password("super")
            user_super.save()
            self.login_user(user_super)
            home_page = self.create_page(title="home", user=user_super)
            # The proper test
            result = get_site_choices()
            self.assertEquals(result, [(1,'example.com')])
            