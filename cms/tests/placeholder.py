# -*- coding: utf-8 -*-
from cms.exceptions import DuplicatePlaceholderWarning
from cms.tests.base import CMSTestCase
from cms.utils.plugins import get_placeholders
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from testapp.placeholderapp.admin import Example1Admin, Example2Admin, \
    Example3Admin, Example4Admin, Example5Admin
from testapp.placeholderapp.models import Example1, Example2, Example3, Example4, \
    Example5


class PlaceholderTestCase(CMSTestCase):
    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self.login_user(u)
        
    def test_01_placeholder_scanning_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_one.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'three']))
        
    def test_02_placeholder_scanning_include(self):
        placeholders = get_placeholders('placeholder_tests/test_two.html')
        self.assertEqual(sorted(placeholders), sorted([u'child', u'three']))
        
    def test_03_placeholder_scanning_double_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_three.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'new_three']))
        
    def test_04_placeholder_scanning_complex(self):
        placeholders = get_placeholders('placeholder_tests/test_four.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'child', u'four']))
        
    def test_05_placeholder_scanning_super(self):
        placeholders = get_placeholders('placeholder_tests/test_five.html')
        self.assertEqual(sorted(placeholders), sorted([u'one', u'extra_one', u'two', u'three']))
        
    def test_06_placeholder_scanning_nested(self):
        placeholders = get_placeholders('placeholder_tests/test_six.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'new_two', u'new_three']))
        
    def test_07_placeholder_scanning_duplicate(self):
        placeholders = self.assertWarns(DuplicatePlaceholderWarning, "Duplicate placeholder found: `one`", get_placeholders, 'placeholder_tests/test_seven.html')
        self.assertEqual(sorted(placeholders), sorted([u'one']))

    def test_08_placeholder_scanning_extend_outside_block(self):
        placeholders = get_placeholders('placeholder_tests/outside.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))
    
    def test_09_fieldsets_requests(self):
        response = self.client.get(reverse('admin:placeholderapp_example1_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example2_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example3_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example4_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example5_add'))
        self.assertEqual(response.status_code, 200)
        
    def test_10_fieldsets(self):
        request = self.get_request('/')
        example1_admin = Example1Admin(Example1, admin.site)
        fieldsets = example1_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        example2_admin = Example1Admin(Example2, admin.site)
        fieldsets = example2_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        example3_admin = Example1Admin(Example3, admin.site)
        fieldsets = example3_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        example4_admin = Example1Admin(Example4, admin.site)
        fieldsets = example4_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        example5_admin = Example1Admin(Example5, admin.site)
        fieldsets = example5_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets), 4)