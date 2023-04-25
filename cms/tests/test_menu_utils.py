from django.http import HttpResponse

from cms.api import create_page, create_page_content
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.mock import AttributeObject
from cms.utils.i18n import get_language_list
from menus.templatetags.menu_tags import PageLanguageUrl
from menus.utils import (
    DefaultLanguageChanger,
    find_selected,
    language_changer_decorator,
)


class DumbPageLanguageUrl(PageLanguageUrl):
    def __init__(self):
        pass


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
        """
        The DefaultLanguageChanger should not try to resolve the url
        for languages not configured.
        """
        cms_page = create_page('en-page', 'nav_playground.html', 'en')

        for language in get_language_list(site_id=1):
            if language not in ('en', 'pt-br', 'es-mx'):
                create_page_content(language, '%s-page' % language, cms_page)

        request = self.get_request(
            path=cms_page.get_absolute_url(),
            language='en',
            page=cms_page,
        )
        urls_expected = [
            '/en/en-page/',
            '/de/de-page/',
            '/fr/fr-page/',
            '/en/en-page/',  # the pt-br url is en because that's a fallback
            '/en/en-page/',  # the es-mx url is en because that's a fallback
        ]
        urls_found = [DefaultLanguageChanger(request)(code)
                      for code in get_language_list(site_id=1)]
        self.assertSequenceEqual(urls_expected, urls_found)

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
