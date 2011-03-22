from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.mock import AttributeObject
from django.http import HttpResponse
from menus.templatetags.menu_tags import PageLanguageUrl
from menus.utils import (simple_language_changer, find_selected, 
    language_changer_decorator)


class DumbPageLanguageUrl(PageLanguageUrl):
    def __init__(self): pass

class MenuUtilsTests(CMSTestCase):
    def get_simple_view(self):
        def myview(request):
            return HttpResponse('')
        return myview
    
    def test_simple_language_changer(self):
        func = self.get_simple_view()
        decorated_view = simple_language_changer(func)
        # check we maintain the view name
        self.assertEqual(func.__name__, decorated_view.__name__)
        request = self.get_request('/', 'en')
        response = decorated_view(request)
        self.assertEqual(response.content, '')
        fake_context = {'request': request}
        tag = DumbPageLanguageUrl()
        output = tag.get_context(fake_context, 'en')
        url = output['content']
        self.assertEqual(url, '/en/')
        output = tag.get_context(fake_context, 'ja')
        url = output['content']
        self.assertEqual(url, '/ja/')
        
    def test_language_changer_decorator(self):
        def lang_changer(lang):
            return "/dummy/"
        decorated_view = language_changer_decorator(lang_changer)(self.get_simple_view())
        request = self.get_request('/some/path/', 'en')
        response = decorated_view(request)
        self.assertEqual(response.content, '')
        fake_context = {'request': request}
        tag = DumbPageLanguageUrl()
        output = tag.get_context(fake_context, 'en')
        url = output['content']
        self.assertEqual(url, '/en/dummy/')
        output = tag.get_context(fake_context, 'ja')
        url = output['content']
        self.assertEqual(url, '/ja/dummy/')
        
        
    def test_find_selected(self):
        subchild = AttributeObject()
        firstchild = AttributeObject(ancestor=True, children=[subchild])
        selectedchild = AttributeObject(selected=True)
        secondchild = AttributeObject(ancestor=True, children=[selectedchild])
        root = AttributeObject(ancestor=True, children=[firstchild, secondchild])
        nodes = [root]
        selected = find_selected(nodes)
        self.assertEqual(selected, selectedchild)
        