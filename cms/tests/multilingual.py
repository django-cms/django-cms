# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page, create_title, publish_page, add_plugin
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect

TEMPLATE_NAME = 'tests/rendering/base.html'


class MultilingualTestCase(SettingsOverrideTestCase):
    settings_overrides = {
        'CMS_TEMPLATES': [(TEMPLATE_NAME, TEMPLATE_NAME), ('extra_context.html', 'extra_context.html'),
                          ('nav_playground.html', 'nav_playground.html')],
        'CMS_MODERATOR': False,
    }


    def test_multilingual_page(self):
        page = create_page("mlpage", "nav_playground.html", "en")
        create_title("de", page.get_title(), page, slug=page.get_slug())
        page.rescan_placeholders()
        page = self.reload(page)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", 'de', body="test")
        add_plugin(placeholder, "TextPlugin", 'en', body="test")
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)
        user = User.objects.create_superuser('super', 'super@django-cms.org', 'super')
        page = publish_page(page, user, True)
        public = page.publisher_public
        placeholder = public.placeholders.all()[0]
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)

    def test_frontend_lang(self):
        with SettingsOverride(CMS_FRONTEND_LANGUAGES=('fr', 'de', 'nl')):
            page = create_page("page1", "nav_playground.html", "en")
            create_title("de", page.get_title(), page, slug=page.get_slug())
            page2 = create_page("page2", "nav_playground.html", "en")
            create_title("de", page2.get_title(), page2, slug=page2.get_slug())
            page3 = create_page("page2", "nav_playground.html", "en")
            create_title("de", page3.get_title(), page3, slug=page3.get_slug())
            page.publish()
            page2.publish()
            page3.publish()
            response = self.client.get("/en/")
            self.assertRedirects(response, "/de/")
            response = self.client.get("/en/page2/")
            self.assertEqual(response.status_code, 404)
            response = self.client.get("/de/")
            self.assertEqual(response.status_code, 200)
            response = self.client.get("/de/page2/")
            self.assertEqual(response.status_code, 200)

    def test_detail_view_404_when_no_language_is_found(self):
        page = create_page("page1", "nav_playground.html", "en")
        create_title("de", page.get_title(), page, slug=page.get_slug())
        page.publish()

        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[],
            CMS_LANGUAGES=[
                ('x-klingon', 'Klingon'),
                ('x-elvish', 'Elvish')
            ], CMS_FRONTEND_LANGUAGES=('x-klingon', 'x-elvish')):
            from cms.views import details

            request = AttributeObject(
                REQUEST={'language': 'x-elvish'},
                GET=[],
                session={},
                path='/',
                current_page=None,
                method='GET',
                COOKIES={},
                META={},
            )
            self.assertRaises(Http404, details, request, '')

    def test_detail_view_fallback_language(self):
        '''
        Ask for a page in elvish (doesn't exist), and assert that it fallsback
        to English
        '''
        page = create_page("page1", "nav_playground.html", "en")
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[],
            CMS_LANGUAGE_CONF={
                'x-elvish': ['x-klingon', 'en', ]
            },
            CMS_LANGUAGES=[
                ('x-klingon', 'Klingon'),
                ('x-elvish', 'Elvish'),
            ],
            CMS_FRONTEND_LANGUAGES=('x-klingon', 'x-elvish')):
            create_title("x-klingon", "futla ak", page, slug=page.get_slug())
            page.publish()
            from cms.views import details

            request = AttributeObject(
                REQUEST={'language': 'x-elvish'},
                GET=[],
                session={},
                path='/',
                current_page=None,
                method='GET',
                COOKIES={},
                META={},
            )

            response = details(request, '')
            self.assertTrue(isinstance(response, HttpResponseRedirect))


