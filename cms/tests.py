from django.test import TestCase
from cms.models import *

class PagesTestCase(TestCase):
    fixtures = ['tests']

    def test_01(self):
        assert(1==1)
        pass
        
