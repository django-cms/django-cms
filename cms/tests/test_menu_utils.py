from urllib.parse import urlencode

from django.http import HttpResponse

from cms.api import create_page, create_page_content
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.mock import AttributeObject
from cms.toolbar.toolbar import CMSToolbar
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

    def test_default_language_changer_uses_cms_path(self):
        """
        On asynchronous toolbar/structure requests ``request.path_info`` points at
        an internal admin/AJAX endpoint, while the viewed page is reported via the
        ``cms_path`` GET query. The language changer must build URLs for the viewed
        page rather than the AJAX endpoint (#8465).
        """
        cms_page = create_page('en-page', 'nav_playground.html', 'en')

        for language in get_language_list(site_id=1):
            if language not in ('en', 'pt-br', 'es-mx'):
                create_page_content(language, '%s-page' % language, cms_page)

        page_url = cms_page.get_absolute_url()
        # Simulate the async toolbar endpoint: ``path_info`` is an admin endpoint
        # and the viewed page is reported via the ``cms_path`` GET query.
        async_path = '/admin/cms/placeholder/object/{pk}/structure/?{query}'.format(
            pk=cms_page.pk,
            query=urlencode({'cms_path': page_url}),
        )
        request = self.get_request(path=async_path, language='en', page=cms_page)
        request.toolbar = CMSToolbar(request)

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

    def test_language_changer_request_path_prefers_toolbar(self):
        """
        ``DefaultLanguageChanger.request_path`` prefers the toolbar's
        ``request_path`` (the viewed page) and falls back to ``path_info``.
        """
        request = self.get_request(path='/admin/some/endpoint/', language='en')

        # No toolbar attached -> falls back to the actual request path.
        self.assertEqual(
            DefaultLanguageChanger(request).request_path,
            '/admin/some/endpoint/',
        )

        # Toolbar request_path (viewed page) takes precedence.
        request.toolbar = CMSToolbar(request, request_path='/en/viewed-page/')
        self.assertEqual(
            DefaultLanguageChanger(request).request_path,
            '/en/viewed-page/',
        )

    def test_toolbar_request_path_honours_cms_path(self):
        """
        ``CMSToolbar.request_path`` is derived from the ``cms_path`` GET query when
        present, falls back to ``path_info`` otherwise, and an explicit
        ``request_path`` always wins.
        """
        cms_page = create_page('en-page', 'nav_playground.html', 'en')
        page_url = cms_page.get_absolute_url()

        async_path = '/admin/cms/placeholder/object/{pk}/structure/?{query}'.format(
            pk=cms_page.pk,
            query=urlencode({'cms_path': page_url}),
        )
        request = self.get_request(path=async_path, language='en', page=cms_page)
        self.assertEqual(CMSToolbar(request).request_path, page_url)

        # Without a cms_path query it falls back to the request path.
        request = self.get_request(path=page_url, language='en', page=cms_page)
        self.assertEqual(CMSToolbar(request).request_path, page_url)

        # An explicitly passed request_path always wins.
        self.assertEqual(
            CMSToolbar(request, request_path='/explicit/').request_path,
            '/explicit/',
        )

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
