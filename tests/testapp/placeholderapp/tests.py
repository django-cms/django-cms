from django.test.testcases import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib import admin

from testapp.placeholderapp.admin import (Example1Admin, Example2Admin,
                                          Example3Admin, Example4Admin,
                                          Example5Admin)
from testapp.placeholderapp.models import (Example1, Example2, Example3,
                                           Example4, Example5)

class MockRequest(object):
    GET = {}

class Example1Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_admin_add_get(self):
        response = self.client.get(reverse('admin:placeholderapp_example1_add'))
        
    def test_admin_get_fieldsets(self):
        request = MockRequest()
        example1_admin = Example1Admin(Example1, admin.site)
        fieldsets = example1_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        
class Example2Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_admin_add_get(self):
        response = self.client.get(reverse('admin:placeholderapp_example2_add'))
    def test_admin_get_fieldsets(self):
        request = MockRequest()
        example2_admin = Example1Admin(Example2, admin.site)
        fieldsets = example2_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        
class Example3Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_admin_add_get(self):
        response = self.client.get(reverse('admin:placeholderapp_example3_add'))
    def test_admin_get_fieldsets(self):
        request = MockRequest()
        example3_admin = Example1Admin(Example3, admin.site)
        fieldsets = example3_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
    
        
class Example4Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_admin_add_get(self):
        response = self.client.get(reverse('admin:placeholderapp_example4_add'))
    def test_admin_get_fieldsets(self):
        request = MockRequest()
        example4_admin = Example1Admin(Example4, admin.site)
        fieldsets = example4_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets),3)
        
class Example5Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_admin_add_get(self):
        response = self.client.get(reverse('admin:placeholderapp_example5_add'))
    def test_admin_get_fieldsets(self):
        request = MockRequest()
        example5_admin = Example1Admin(Example5, admin.site)
        fieldsets = example5_admin.get_fieldsets(request)
        self.assertEqual(len(fieldsets), 4)
