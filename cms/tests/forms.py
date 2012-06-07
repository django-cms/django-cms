# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.admin import forms
from cms.admin.forms import PageUserForm
from cms.api import create_page, create_page_user
from cms.forms.fields import PageSelectFormField, SuperLazyIterator
from cms.forms.utils import (get_site_choices, get_page_choices, 
    update_site_and_page_choices)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache

class Mock_PageSelectFormField(PageSelectFormField): 
    def __init__(self, required=False):
        # That's to have a proper mock object, without having to resort
        # to dirtier tricks. We want to test *just* compress here.
        self.required = required
        self.error_messages = {}
        self.error_messages['invalid_page'] = 'Invalid_page'

class FormsTestCase(CMSTestCase):
    def setUp(self):
        cache.clear()
        
    def test_get_site_choices(self):
        result = get_site_choices()
        self.assertEquals(result, [])
        
    def test_get_page_choices(self):
        result = get_page_choices()
        self.assertEquals(result, [('', '----')])
        
    def test_get_site_choices_without_moderator(self):
        with SettingsOverride(CMS_MODERATOR=False):
            result = get_site_choices()
            self.assertEquals(result, [])
            
    def test_get_site_choices_without_moderator_with_superuser(self):
        with SettingsOverride(CMS_MODERATOR=False):
            # boilerplate (creating a page)
            user_super = User(username="super", is_staff=True, is_active=True, 
                is_superuser=True)
            user_super.set_password("super")
            user_super.save()
            with self.login_user_context(user_super):
                create_page("home", "nav_playground.html", "en", created_by=user_super)
                # The proper test
                result = get_site_choices()
                self.assertEquals(result, [(1,'example.com')])
            
    def test_compress_function_raises_when_page_is_none(self):
        raised = False
        try:
            fake_field = Mock_PageSelectFormField(required=True)
            data_list = (0, None) #(site_id, page_id) dsite-id is not used
            fake_field.compress(data_list)
            self.fail('compress function didn\'t raise!')
        except forms.ValidationError:
            raised = True
        self.assertTrue(raised)
        
    def test_compress_function_returns_none_when_not_required(self):
        fake_field = Mock_PageSelectFormField(required=False)
        data_list = (0, None) #(site_id, page_id) dsite-id is not used
        result = fake_field.compress(data_list)
        self.assertEquals(result, None)
        
    def test_compress_function_returns_none_when_no_data_list(self):
        fake_field = Mock_PageSelectFormField(required=False)
        data_list = None
        result = fake_field.compress(data_list)
        self.assertEquals(result, None)
        
    def test_compress_function_gets_a_page_when_one_exists(self):
        # boilerplate (creating a page)
        user_super = User(username="super", is_staff=True, is_active=True, 
                          is_superuser=True)
        user_super.set_password("super")
        user_super.save()
        with self.login_user_context(user_super):
            home_page = create_page("home", "nav_playground.html", "en", created_by=user_super)
            # The actual test
            fake_field = Mock_PageSelectFormField()
            data_list = (0, home_page.pk) #(site_id, page_id) dsite-id is not used
            result = fake_field.compress(data_list)
            self.assertEquals(home_page,result)
            
    def test_update_site_and_page_choices(self):
        with SettingsOverride(CMS_MODERATOR=False):
            Site.objects.all().delete()
            site = Site.objects.create(domain='http://www.django-cms.org', name='Django CMS')
            page1 = create_page('Page 1', 'nav_playground.html', 'en', site=site)
            page2 = create_page('Page 2', 'nav_playground.html', 'de', site=site)
            page3 = create_page('Page 3', 'nav_playground.html', 'en',
                         site=site, parent=page1)
            # enfore the choices to be casted to a list
            site_choices, page_choices = [list(bit) for bit in update_site_and_page_choices('en')]
            self.assertEqual(page_choices, [
                ('', '----'),
                (site.name, [
                    (page1.pk, 'Page 1'),
                    (page3.pk, '&nbsp;&nbsp;Page 3'),
                    (page2.pk, 'Page 2'),
                ])
            ])
            self.assertEqual(site_choices, [(site.pk, site.name)])

        
    def test_superlazy_iterator_behaves_properly_for_sites(self):
        normal_result = get_site_choices()
        lazy_result = SuperLazyIterator(get_site_choices)
        
        self.assertEquals(normal_result, list(lazy_result))
        
    def test_superlazy_iterator_behaves_properly_for_pages(self):
        normal_result = get_page_choices()
        lazy_result = SuperLazyIterator(get_page_choices)
        
        self.assertEquals(normal_result, list(lazy_result))

    def test_page_user_form_initial(self):
        myuser = User.objects.create_superuser("myuser", "myuser@django-cms.org", "myuser")
        user = create_page_user(myuser, myuser, grant_all=True)
        puf = PageUserForm(instance=user)
        names = ['can_add_page', 'can_change_page', 'can_delete_page',
                 'can_add_pageuser', 'can_change_pageuser',
                 'can_delete_pageuser', 'can_add_pagepermission',
                 'can_change_pagepermission', 'can_delete_pagepermission']
        for name in names:
            self.assertTrue(puf.initial.get(name, False))
