from django.test.testcases import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

class Example1Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_example1_(self):
        response = self.client.get(reverse('admin:placeholderapp_example1_add'))
        
class Example2Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_example1_(self):
        response = self.client.get(reverse('admin:placeholderapp_example2_add'))
        
class Example3Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_example1_(self):
        response = self.client.get(reverse('admin:placeholderapp_example3_add'))
        
class Example4Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_example1_(self):
        response = self.client.get(reverse('admin:placeholderapp_example4_add'))
        
class Example5Test(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('yml', 'yml@yml.fr', 'yml')
        self.client.login(username='yml', password='yml')
    def tearDown(self):
        self.client.logout()
    
    def test_example1_(self):
        response = self.client.get(reverse('admin:placeholderapp_example5_add'))
