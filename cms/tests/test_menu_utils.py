from django.http import HttpResponse

from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.mock import AttributeObject
from menus.templatetags.menu_tags import PageLanguageUrl
from menus.utils import find_selected, language_changer_decorator


class DumbPageLanguageUrl(PageLanguageUrl):
    def __init__(self): pass


class MenuUtilsTests(CMSTestCase):
    def get_simple_view(self):
        def myview(request):
            return HttpResponse('')
        return myview

    def test_reverse_in_changer(self):
        response = self.client.get('/en/sample/login/')
        self.assertContains(response, '<h1>/fr/sample/login/</h1>')

        response = self.client.get('/en/sample/login_other/')
        self.assertContains(response, '<h1>/fr/sample/login_other/</h1>')

        response = self.client.get('/en/sample/login3/')
        self.assertContains(response, '<h1>/fr/sample/login3/</h1>')

    def test_default_language_changer(self):
        view = self.get_simple_view()
        # check we maintain the view name
        self.assertEqual(view.__name__, view.__name__)
        request = self.get_request('/en/', 'en')
        response = view(request)
        self.assertEqual(response.content, b'')
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
            return "/%s/dummy/" % lang
        decorated_view = language_changer_decorator(lang_changer)(self.get_simple_view())
        request = self.get_request('/some/path/', 'en')
        response = decorated_view(request)
        self.assertEqual(response.content, b'')
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
