from __future__ import with_statement
import copy
from django.test import RequestFactory, TestCase
import os
from cms.api import create_page, create_title, add_plugin
from cms.models.pagemodel import Page, Placeholder
from cms.plugins.text.cms_plugins import TextPlugin
from cms.templatetags.cms_tags import (get_site_id, _get_page_by_untyped_arg,
    _show_placeholder_for_page)
from cms.test_utils.fixtures.templatetags import TwoPagesFixture
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils import get_cms_setting
from cms.utils.plugins import get_placeholders
from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.template import RequestContext, Context
from django.template.base import Template
from django.utils.html import escape
from django.contrib.auth.models import User


class TemplatetagTests(TestCase):
    def test_get_site_id_from_nothing(self):
        with SettingsOverride(SITE_ID=10):
            self.assertEqual(10, get_site_id(None))

    def test_get_site_id_from_int(self):
        self.assertEqual(10, get_site_id(10))

    def test_get_site_id_from_site(self):
        site = Site()
        site.id = 10
        self.assertEqual(10, get_site_id(site))

    def test_get_site_id_from_str_int(self):
        self.assertEqual(10, get_site_id('10'))

    def test_get_site_id_from_str(self):
        with SettingsOverride(SITE_ID=10):
            self.assertEqual(10, get_site_id("something"))

    def test_unicode_placeholder_name_fails_fast(self):
        self.assertRaises(ImproperlyConfigured, get_placeholders, 'unicode_placeholder.html')

    def test_page_attribute_tag_escapes_content(self):
        script = '<script>alert("XSS");</script>'

        class FakePage(object):
            def get_page_title(self, *args, **kwargs):
                return script

        class FakeRequest(object):
            current_page = FakePage()
            REQUEST = {'language': 'en'}

        request = FakeRequest()
        template = Template('{% load cms_tags %}{% page_attribute page_title %}')
        context = Context({'request': request})
        output = template.render(context)
        self.assertNotEqual(script, output)
        self.assertEqual(escape(script), output)


class TemplatetagDatabaseTests(TwoPagesFixture, SettingsOverrideTestCase):
    def _getfirst(self):
        return Page.objects.public().get(title_set__title='first')

    def _getsecond(self):
        return Page.objects.public().get(title_set__title='second')

    def test_get_page_by_untyped_arg_none(self):
        control = self._getfirst()
        request = self.get_request('/')
        request.current_page = control
        page = _get_page_by_untyped_arg(None, request, 1)
        self.assertEqual(page, control)

    def test_get_page_by_pk_arg_edit_mode(self):
        control = self._getfirst()
        request = self.get_request('/')
        request.GET = {"edit": ''}
        user = User(username="admin", password="admin", is_superuser=True, is_staff=True, is_active=True)
        user.save()
        request.current_page = control
        request.user = user
        page = _get_page_by_untyped_arg(control.pk, request, 1)
        self.assertEqual(page, control.publisher_draft)

    def test_get_page_by_untyped_arg_page(self):
        control = self._getfirst()
        request = self.get_request('/')
        page = _get_page_by_untyped_arg(control, request, 1)
        self.assertEqual(page, control)

    def test_get_page_by_untyped_arg_reverse_id(self):
        second = self._getsecond()
        request = self.get_request('/')
        page = _get_page_by_untyped_arg("myreverseid", request, 1)
        self.assertEqual(page, second)

    def test_get_page_by_untyped_arg_dict(self):
        second = self._getsecond()
        request = self.get_request('/')
        page = _get_page_by_untyped_arg({'pk': second.pk}, request, 1)
        self.assertEqual(page, second)

    def test_get_page_by_untyped_arg_dict_fail_debug(self):
        with SettingsOverride(DEBUG=True):
            request = self.get_request('/')
            self.assertRaises(Page.DoesNotExist,
                              _get_page_by_untyped_arg, {'pk': 1003}, request, 1
            )
            self.assertEqual(len(mail.outbox), 0)

    def test_get_page_by_untyped_arg_dict_fail_nodebug_do_email(self):
        with SettingsOverride(SEND_BROKEN_LINK_EMAILS=True, DEBUG=False,
                              MANAGERS=[("Jenkins", "tests@django-cms.org")]):
            request = self.get_request('/')
            page = _get_page_by_untyped_arg({'pk': 1003}, request, 1)
            self.assertEqual(page, None)
            self.assertEqual(len(mail.outbox), 1)

    def test_get_page_by_untyped_arg_dict_fail_nodebug_no_email(self):
        with SettingsOverride(SEND_BROKEN_LINK_EMAILS=False, DEBUG=False,
                              MANAGERS=[("Jenkins", "tests@django-cms.org")]):
            request = self.get_request('/')
            page = _get_page_by_untyped_arg({'pk': 1003}, request, 1)
            self.assertEqual(page, None)
            self.assertEqual(len(mail.outbox), 0)

    def test_get_page_by_untyped_arg_fail(self):
        request = self.get_request('/')
        self.assertRaises(TypeError, _get_page_by_untyped_arg, [], request, 1)

    def test_show_placeholder_for_page_placeholder_does_not_exist(self):
        """
        Verify ``show_placeholder`` correctly handles being given an
        invalid identifier.
        """
        with SettingsOverride(DEBUG=True):
            request = HttpRequest()
            request.REQUEST = {}
            request.session = {}
            request.user = User()
            self.assertRaises(Placeholder.DoesNotExist,
                              _show_placeholder_for_page,
                              RequestContext(request),
                              'does_not_exist',
                              'myreverseid')
        with SettingsOverride(DEBUG=False):
            content = _show_placeholder_for_page(RequestContext(request),
                                                 'does_not_exist', 'myreverseid')
            self.assertEqual(content['content'], '')

    def test_untranslated_language_url(self):
        """ Tests page_language_url templatetag behavior when used on a page
          without the requested translation, both when CMS_HIDE_UNTRANSLATED is
          True and False.
          When True it should return the root page URL if the current page is
           untranslated (PR #1125)

        """
        page_1 = create_page('Page 1', 'nav_playground.html', 'en', published=True,
                             in_navigation=True, reverse_id='page1')
        create_title("de", "Seite 1", page_1, slug="seite-1")
        page_1.publish()
        page_2 = create_page('Page 2', 'nav_playground.html', 'en', page_1, published=True,
                             in_navigation=True, reverse_id='page2')
        create_title("de", "Seite 2", page_2, slug="seite-2")
        page_2.publish()
        page_3 = create_page('Page 3', 'nav_playground.html', 'en', page_2, published=True,
                             in_navigation=True, reverse_id='page3')
        tpl = Template("{% load menu_tags %}{% page_language_url 'de' %}")
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][1]['hide_untranslated'] = False
        with SettingsOverride(CMS_LANGUAGES=lang_settings):
            context = self.get_context(page_2.get_absolute_url())
            context['request'].current_page = page_2
            res = tpl.render(context)
            self.assertEqual(res, "/de/seite-2/")

            # Default configuration has CMS_HIDE_UNTRANSLATED=False
            context = self.get_context(page_2.get_absolute_url())
            context['request'].current_page = page_2.publisher_public
            res = tpl.render(context)
            self.assertEqual(res, "/de/seite-2/")

            context = self.get_context(page_3.get_absolute_url())
            context['request'].current_page = page_3.publisher_public
            res = tpl.render(context)
            self.assertEqual(res, "/de/page-3/")
        lang_settings[1][1]['hide_untranslated'] = True

        with SettingsOverride(CMS_LANGUAGES=lang_settings):
            context = self.get_context(page_2.get_absolute_url())
            context['request'].current_page = page_2.publisher_public
            res = tpl.render(context)
            self.assertEqual(res, "/de/seite-2/")

            context = self.get_context(page_3.get_absolute_url())
            context['request'].current_page = page_3.publisher_public
            res = tpl.render(context)
            self.assertEqual(res, "/de/")


class NoFixtureDatabaseTemplateTagTests(TestCase):
    def test_cached_show_placeholder_sekizai(self):
        from django.core.cache import cache

        cache.clear()
        from cms.test_utils import project

        template_dir = os.path.join(os.path.dirname(project.__file__), 'templates', 'alt_plugin_templates',
                                    'show_placeholder')
        page = create_page('Test', 'col_two.html', 'en')
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, TextPlugin, 'en', body='HIDDEN')
        request = RequestFactory().get('/')
        with SettingsOverride(TEMPLATE_DIRS=[template_dir]):
            template = Template(
                "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'en' 1 %}{% render_block 'js' %}")
            context = RequestContext(request, {'page': page, 'slot': placeholder.slot})
            output = template.render(context)
            self.assertIn('JAVASCRIPT', output)
            context = RequestContext(request, {'page': page, 'slot': placeholder.slot})
            output = template.render(context)
            self.assertIn('JAVASCRIPT', output)

    def test_show_placeholder_for_page_marks_output_safe(self):
        from django.core.cache import cache

        cache.clear()
        page = create_page('Test', 'col_two.html', 'en')
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        request = RequestFactory().get('/')
        template = Template(
            "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'en' 1 %}{% render_block 'js' %}")
        context = RequestContext(request, {'page': page, 'slot': placeholder.slot})
        with self.assertNumQueries(4):
            output = template.render(context)
        self.assertIn('<b>Test</b>', output)
        context = RequestContext(request, {'page': page, 'slot': placeholder.slot})
        with self.assertNumQueries(0):
            output = template.render(context)
        self.assertIn('<b>Test</b>', output)

    def test_cached_show_placeholder_preview(self):
        from django.core.cache import cache

        cache.clear()
        page = create_page('Test', 'col_two.html', 'en')
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        request = RequestFactory().get('/')
        template = Template(
            "{% load cms_tags %}{% show_placeholder slot page 'en' 1 %}")
        context = RequestContext(request, {'page': page, 'slot': placeholder.slot})
        with self.assertNumQueries(4):
            output = template.render(context)
        self.assertIn('<b>Test</b>', output)
        add_plugin(placeholder, TextPlugin, 'en', body='<b>Test2</b>')
        request = RequestFactory().get('/?preview')
        context = RequestContext(request, {'page': page, 'slot': placeholder.slot})
        with self.assertNumQueries(4):
            output = template.render(context)
        self.assertIn('<b>Test2</b>', output)