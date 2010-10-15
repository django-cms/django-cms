# -*- coding: utf-8 -*-
from cms.exceptions import DuplicatePlaceholderWarning
from cms.tests.base import CMSTestCase
from cms.utils.plugins import get_placeholders
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template import TemplateSyntaxError
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
        admins = [
            (Example1, 2),
            (Example2, 3),
            (Example3, 3),
            (Example4, 3),
            (Example5, 4),
        ]
        for model, fscount in admins:
            ainstance = admin.site._registry[model]
            fieldsets = ainstance.get_fieldsets(request)
            form = ainstance.get_form(request, None)
            phfields = ainstance._get_placeholder_fields(form)
            self.assertEqual(len(fieldsets), fscount, (
                "Asserting fieldset count for %s. Got %s instead of %s: %s. "
                "Using %s." % (model.__name__, len(fieldsets),
                    fscount, fieldsets, ainstance.__class__.__name__)      
            ))
            for label, fieldset in fieldsets:
                fields = list(fieldset['fields'])
                for field in fields:
                    if field in phfields:
                        self.assertTrue(len(fields) == 1)
                        self.assertTrue('plugin-holder' in fieldset['classes'])
                        self.assertTrue('plugin-holder-nopage' in fieldset['classes'])
                        phfields.remove(field)
            self.assertEqual(phfields, [])
            
    def test_11_placeholder_scanning_fail(self):
        self.assertRaises(TemplateSyntaxError, get_placeholders, 'placeholder_tests/test_eleven.html')