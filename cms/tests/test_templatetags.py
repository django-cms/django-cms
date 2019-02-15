from copy import deepcopy
import os

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils.html import escape
from django.utils.timezone import now
from djangocms_text_ckeditor.cms_plugins import TextPlugin

from mock import patch

import cms
from cms.api import create_page, create_title, add_plugin
from cms.middleware.toolbar import ToolbarMiddleware
from cms.models import Page, Placeholder
from cms.templatetags.cms_tags import (
    _get_page_by_untyped_arg,
    _show_placeholder_by_id,
    render_plugin,
)
from cms.templatetags.cms_js_tags import json_filter
from cms.test_utils.fixtures.templatetags import TwoPagesFixture
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.toolbar import CMSToolbar
from cms.utils import get_site_id
from cms.utils.conf import get_cms_setting
from cms.utils.placeholder import get_placeholders
from sekizai.context import SekizaiContext


class TemplatetagTests(CMSTestCase):

    def test_get_site_id_from_nothing(self):
        with self.settings(SITE_ID=10):
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
        with self.settings(SITE_ID=10):
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
            GET = {'language': 'en'}

        request = FakeRequest()
        template = '{% load cms_tags %}{% page_attribute page_title %}'
        output = self.render_template_obj(template, {}, request)
        self.assertNotEqual(script, output)
        self.assertEqual(escape(script), output)

    def test_json_encoder(self):
        self.assertEqual(json_filter(True), 'true')
        self.assertEqual(json_filter(False), 'false')
        self.assertEqual(json_filter([1, 2, 3]), '[1, 2, 3]')
        self.assertEqual(json_filter((1, 2, 3)), '[1, 2, 3]')
        filtered_dict = json_filter({'item1': 1, 'item2': 2, 'item3': 3})
        self.assertTrue('"item1": 1' in filtered_dict)
        self.assertTrue('"item2": 2' in filtered_dict)
        self.assertTrue('"item3": 3' in filtered_dict)
        today = now().today()
        self.assertEqual('"%s"' % today.isoformat()[:-3], json_filter(today))

    def test_static_with_version(self):
        expected = '<script src="/static/cms/css/%(version)s/cms.base.css" type="text/javascript"></script>'
        expected = expected % {'version': cms.__version__}

        template = (
            """{% load cms_static %}<script src="{% static_with_version "cms/css/cms.base.css" %}" """
            """type="text/javascript"></script>"""
        )

        output = self.render_template_obj(template, {}, None)
        self.assertEqual(expected, output)

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.ManifestStaticFilesStorage')
    @patch('django.contrib.staticfiles.storage.staticfiles_storage')
    def test_static_with_version_manifest(self, mock_storage):
        """
        Check that static files are looked up at the location where they are
        stored when using static file manifests.
        """
        mock_storage.url.side_effect = lambda x: '/static/' + x

        template = (
            """{% load staticfiles cms_static %}<script src="{% static_with_version "cms/css/cms.base.css" %}" """
            """type="text/javascript"></script>"""
        )

        output = self.render_template_obj(template, {}, None)
        # If the manifest is used for looking up the static file (Django 1.10
        # and later), it needs to be looked up with a proper path.
        versioned_filename = 'cms/css/%s/cms.base.css' % cms.__version__
        if mock_storage.url.called:
            mock_storage.url.assert_called_with(versioned_filename)

        expected = '<script src="/static/%s" type="text/javascript"></script>'
        expected = expected % versioned_filename
        self.assertEqual(expected, output)


class TemplatetagDatabaseTests(TwoPagesFixture, CMSTestCase):
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
        user = self._create_user("admin", True, True)
        request.current_page = control
        request.user = user
        middleware = ToolbarMiddleware()
        middleware.process_request(request)
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
        with self.settings(DEBUG=True):
            request = self.get_request('/')
            self.assertRaises(Page.DoesNotExist,
                              _get_page_by_untyped_arg, {'pk': 1003}, request, 1
            )
            self.assertEqual(len(mail.outbox), 0)

    def test_get_page_by_untyped_arg_dict_fail_nodebug_do_email(self):
        with self.settings(SEND_BROKEN_LINK_EMAILS=True, DEBUG=False,
                           MANAGERS=[("Jenkins", "tests@django-cms.org")]):
            request = self.get_request('/')
            page = _get_page_by_untyped_arg({'pk': 1003}, request, 1)
            self.assertEqual(page, None)
            self.assertEqual(len(mail.outbox), 1)

    def test_get_page_by_untyped_arg_dict_fail_nodebug_no_email(self):
        with self.settings(SEND_BROKEN_LINK_EMAILS=False, DEBUG=False,
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

        with self.settings(DEBUG=True):
            context = self.get_context('/')

            self.assertRaises(Placeholder.DoesNotExist, _show_placeholder_by_id,
                              context, 'does_not_exist', 'myreverseid')
        with self.settings(DEBUG=False):
            content = _show_placeholder_by_id(context, 'does_not_exist', 'myreverseid')
            self.assertEqual(content, '')

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
        page_1.publish('en')
        page_1.publish('de')
        page_2 = create_page('Page 2', 'nav_playground.html', 'en', page_1, published=True,
                             in_navigation=True, reverse_id='page2')
        create_title("de", "Seite 2", page_2, slug="seite-2")
        page_2.publish('en')
        page_2.publish('de')
        page_3 = create_page('Page 3', 'nav_playground.html', 'en', page_2, published=True,
                             in_navigation=True, reverse_id='page3')
        tpl = "{% load menu_tags %}{% page_language_url 'de' %}"
        lang_settings = deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][1]['hide_untranslated'] = False
        with self.settings(CMS_LANGUAGES=lang_settings):
            context = self.get_context(page_2.get_absolute_url())
            context['request'].current_page = page_2
            res = self.render_template_obj(tpl, context.__dict__, context['request'])
            self.assertEqual(res, "/de/seite-2/")

            # Default configuration has CMS_HIDE_UNTRANSLATED=False
            context = self.get_context(page_2.get_absolute_url())
            context['request'].current_page = page_2.publisher_public
            res = self.render_template_obj(tpl, context.__dict__, context['request'])
            self.assertEqual(res, "/de/seite-2/")

            context = self.get_context(page_3.get_absolute_url())
            context['request'].current_page = page_3.publisher_public
            res = self.render_template_obj(tpl, context.__dict__, context['request'])
            self.assertEqual(res, "/en/page-3/")
        lang_settings[1][1]['hide_untranslated'] = True

        with self.settings(CMS_LANGUAGES=lang_settings):
            context = self.get_context(page_2.get_absolute_url())
            context['request'].current_page = page_2.publisher_public
            res = self.render_template_obj(tpl, context.__dict__, context['request'])
            self.assertEqual(res, "/de/seite-2/")

            context = self.get_context(page_3.get_absolute_url())
            context['request'].current_page = page_3.publisher_public
            res = self.render_template_obj(tpl, context.__dict__, context['request'])
            self.assertEqual(res, "/de/")

    def test_create_placeholder_if_not_exist_in_template(self):
        """
        Tests that adding a new placeholder to a an exising page's template
        creates the placeholder.
        """
        page = create_page('Test', 'col_two.html', 'en')
        # I need to make it seem like the user added another placeholder to the SAME template.
        page._template_cache = 'col_three.html'

        request = self.get_request(page=page)
        context = SekizaiContext()
        context['request'] = request

        self.assertObjectDoesNotExist(page.placeholders.all(), slot='col_right')
        context = self.get_context(page=page)
        renderer = self.get_content_renderer(request)
        renderer.render_page_placeholder(
            'col_right',
            context,
            inherit=False,
            page=page,
        )
        self.assertObjectExist(page.placeholders.all(), slot='col_right')


class NoFixtureDatabaseTemplateTagTests(CMSTestCase):

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
        request.user = self.get_staff_user_with_no_permissions()
        request.current_page = page
        override = {'TEMPLATES': deepcopy(settings.TEMPLATES)}
        override['TEMPLATES'][0]['DIRS'] = [template_dir]
        with self.settings(**override):
            template = "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'en' 1 %}{% render_block 'js' %}"
            output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
            self.assertIn('JAVASCRIPT', output)

    def test_show_placeholder_lang_parameter(self):
        from django.core.cache import cache

        cache.clear()
        page = create_page('Test', 'col_two.html', 'en')
        create_title('fr', 'Fr Test', page)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, TextPlugin, 'en', body='<b>En Test</b>')
        add_plugin(placeholder, TextPlugin, 'fr', body='<b>Fr Test</b>')

        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        request.current_page = page

        template = "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'en' 1 %}{% render_block 'js' %}"
        output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>En Test</b>', output)

        template = "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'fr' 1 %}{% render_block 'js' %}"
        output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>Fr Test</b>', output)

        # Cache is now primed for both languages
        template = "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'en' 1 %}{% render_block 'js' %}"
        output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>En Test</b>', output)

        template = "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'fr' 1 %}{% render_block 'js' %}"
        output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>Fr Test</b>', output)

    def test_show_placeholder_for_page_marks_output_safe(self):
        from django.core.cache import cache

        cache.clear()
        page = create_page('Test', 'col_two.html', 'en')
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')

        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        request.current_page = page

        template = "{% load cms_tags sekizai_tags %}{% show_placeholder slot page 'en' 1 %}{% render_block 'js' %}"
        with self.assertNumQueries(3):
            output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>Test</b>', output)

        with self.assertNumQueries(1):
            output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>Test</b>', output)

    def test_cached_show_placeholder_preview(self):
        from django.core.cache import cache
        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        request = RequestFactory().get('/')
        user = self._create_user("admin", True, True)
        request.current_page = page.publisher_public
        request.user = user
        template = "{% load cms_tags %}{% show_placeholder slot page 'en' 1 %}"
        with self.assertNumQueries(3):
            output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>Test</b>', output)
        add_plugin(placeholder, TextPlugin, 'en', body='<b>Test2</b>')
        request = RequestFactory().get('/?preview')
        request.current_page = page
        request.user = user
        with self.assertNumQueries(3):
            output = self.render_template_obj(template, {'page': page, 'slot': placeholder.slot}, request)
        self.assertIn('<b>Test2</b>', output)

    def test_render_plugin(self):
        from django.core.cache import cache
        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        template = "{% load cms_tags %}{% render_plugin plugin %}"
        request = RequestFactory().get('/')
        user = self._create_user("admin", True, True)
        request.user = user
        request.current_page = page
        request.session = {}
        request.toolbar = CMSToolbar(request)
        with self.assertNumQueries(0):
            output = self.render_template_obj(template, {'plugin': plugin}, request)
        self.assertIn('<b>Test</b>', output)

    def test_render_plugin_editable(self):
        from django.core.cache import cache
        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        template = "{% load cms_tags %}{% render_plugin plugin %}"
        request = RequestFactory().get('/')
        user = self._create_user("admin", True, True)
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        request.toolbar.show_toolbar = True
        output = self.render_template_obj(template, {'plugin': plugin}, request)
        expected = (
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}"></template>'
            '<b>Test</b>'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}"></template>'
        )
        self.assertEqual(output, expected.format(plugin.pk))

    def test_render_plugin_not_editable(self):
        from django.core.cache import cache
        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        template = "{% load cms_tags %}{% render_plugin plugin %}"
        request = RequestFactory().get('/')
        user = self._create_user("admin", True, True)
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': False}
        request.toolbar = CMSToolbar(request)
        request.toolbar.show_toolbar = True
        output = self.render_template_obj(template, {'plugin': plugin}, request)
        self.assertEqual('<b>Test</b>', output)

    def test_render_plugin_no_context(self):
        placeholder = Placeholder.objects.create(slot='test')
        plugin = add_plugin(placeholder, TextPlugin, 'en', body='Test')
        superuser = self.get_superuser()
        request = RequestFactory().get('/')
        request.current_page = None
        request.user = superuser
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        context = SekizaiContext({
            'request': request,
        })
        output = render_plugin(context, plugin)
        self.assertEqual(
            output,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}"></template>Test<template class="cms-plugin cms-plugin-end cms-plugin-{0}"></template>'.format(
                plugin.pk
            )
        )

    def test_render_placeholder_with_no_page(self):
        page = create_page('Test', 'col_two.html', 'en', published=True)
        template = "{% load cms_tags %}{% placeholder test or %}< --- empty --->{% endplaceholder %}"
        request = RequestFactory().get('/asdadsaasd/')
        user = self.get_superuser()
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        request.toolbar.is_staff = True
        with self.assertNumQueries(2):
            output = self.render_template_obj(template, {}, request)
            self.assertEqual(output, '< --- empty --->')

    def test_render_placeholder_as_var(self):
        page = create_page('Test', 'col_two.html', 'en', published=True)
        template = "{% load cms_tags %}{% placeholder test or %}< --- empty --->{% endplaceholder %}"
        request = RequestFactory().get('/asdadsaasd/')
        user = self.get_superuser()
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        request.toolbar.is_staff = True
        with self.assertNumQueries(2):
            output = self.render_template_obj(template, {}, request)
            self.assertEqual(output, '< --- empty --->')

    def test_render_model_with_deferred_fields(self):
        from django.core.cache import cache
        from cms.test_utils.project.sampleapp.models import Category

        Category.objects.create(name='foo', depth=1)
        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        template = "{% load cms_tags %}{% render_model category 'name' %}"
        user = self._create_user("admin", True, True)
        request = RequestFactory().get('/')
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        request.toolbar.is_staff = True
        category = Category.objects.only('name').get()
        output = self.render_template_obj(template, {'category': category}, request)
        expected = "cms-plugin cms-plugin-start cms-plugin-sampleapp-category-name-%d cms-render-model" % category.pk
        self.assertIn(expected, output)

        # Now test that it does NOT render when not in edit mode
        request = RequestFactory().get('/')
        request.user = user
        request.current_page = page
        request.session = {}
        request.toolbar = CMSToolbar(request)
        with self.assertNumQueries(0):
            output = self.render_template_obj(template, {'category': category}, request)
        expected = 'foo'
        self.assertEqual(expected, output)

    def test_render_model_add(self):
        from django.core.cache import cache
        from cms.test_utils.project.sampleapp.models import Category

        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        template = "{% load cms_tags %}{% render_model_add category %}"
        user = self._create_user("admin", True, True)
        request = RequestFactory().get(page.get_absolute_url())
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        request.toolbar.is_staff = True
        with self.assertNumQueries(0):
            output = self.render_template_obj(template, {'category': Category()}, request)
        expected_start = '<template class="cms-plugin cms-plugin-start cms-plugin-sampleapp-category-add-0 cms-render-model-add"></template>'
        expected_end = '<template class="cms-plugin cms-plugin-end cms-plugin-sampleapp-category-add-0 cms-render-model-add"></template>'
        self.assertIn(expected_start, output)
        self.assertIn(expected_end, output)

        # Now test that it does NOT render when not in edit mode
        request = RequestFactory().get(page.get_absolute_url())
        request.user = user
        request.current_page = page
        request.session = {}
        request.toolbar = CMSToolbar(request)
        with self.assertNumQueries(0):
            output = self.render_template_obj(template, {'category': Category()}, request)
        expected = ''
        self.assertEqual(expected, output)

    def test_render_model_add_block(self):
        from django.core.cache import cache
        from cms.test_utils.project.sampleapp.models import Category

        cache.clear()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        template = "{% load cms_tags %}{% render_model_add_block category %}wrapped{% endrender_model_add_block %}"
        user = self._create_user("admin", True, True)
        request = RequestFactory().get(page.get_absolute_url())
        request.user = user
        request.current_page = page
        request.session = {'cms_edit': True}
        request.toolbar = CMSToolbar(request)
        request.toolbar.is_staff = True
        with self.assertNumQueries(0):
            output = self.render_template_obj(template, {'category': Category()}, request)
        expected_start = '<template class="cms-plugin cms-plugin-start cms-plugin-sampleapp-category-add-0 '
        'cms-render-model-add"></template>'
        expected_end = '<template class="cms-plugin cms-plugin-end cms-plugin-sampleapp-category-add-0 '
        'cms-render-model-add"></template>'
        self.assertIn(expected_start, output)
        self.assertIn(expected_end, output)

        # Now test that it does NOT render when not in edit mode
        request = RequestFactory().get(page.get_absolute_url())
        request.user = user
        request.current_page = page
        request.session = {}
        request.toolbar = CMSToolbar(request)
        with self.assertNumQueries(0):
            output = self.render_template_obj(template, {'category': Category()}, request)
        expected = 'wrapped'
        self.assertEqual(expected, output)
