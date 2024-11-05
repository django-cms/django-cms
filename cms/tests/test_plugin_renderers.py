from collections import deque

from django.template import Context
from django.test.utils import override_settings

from cms.api import add_plugin, create_page
from cms.models import CMSPlugin
from cms.plugin_rendering import (
    ContentRenderer,
    LegacyRenderer,
    StructureRenderer,
)
from cms.test_utils.testcases import CMSTestCase


class TestStructureRenderer(CMSTestCase):
    renderer_class = StructureRenderer

    def get_renderer(self, path=None, language='en', page=None):
        if page and path is None:
            path = page.get_absolute_url(language)
        request = self.get_request(path, language, page=page)
        return self.renderer_class(request)

    def test_get_plugin_class_cache(self):
        plugin = CMSPlugin(plugin_type='MultiColumnPlugin')
        renderer = self.get_renderer()
        plugin_class = renderer.get_plugin_class(plugin)
        self.assertIn('MultiColumnPlugin', renderer._cached_plugin_classes)
        self.assertEqual(plugin_class.__name__, 'MultiColumnPlugin')
        self.assertEqual(renderer._cached_plugin_classes['MultiColumnPlugin'], plugin_class)

    def test_get_placeholder_plugin_menu(self):
        cms_page = create_page("page", 'nav_playground.html', "en")
        superuser = self.get_superuser()
        placeholder_1 = cms_page.get_placeholders("en").get(slot='body')

        with self.login_user_context(superuser):
            renderer = self.get_renderer()
            plugin_menu = renderer.get_placeholder_plugin_menu(placeholder_1)
            expected = '<div class="cms-submenu-item cms-submenu-item-title"><span>Multi Columns</span></div>'
            self.assertTrue(expected in plugin_menu)

    def test_render_placeholder_toolbar_js(self):
        cms_page = create_page("page", 'nav_playground.html', "en")
        renderer = self.get_renderer()
        placeholder = cms_page.get_placeholders("en").get(slot='body')
        content = renderer.get_placeholder_toolbar_js(placeholder, cms_page)

        expected_bits = [
            '"MultiColumnPlugin"',
            '"addPluginHelpTitle": "Add plugin to placeholder \\"Body\\""',
            '"name": "Body"',
            f'"placeholder_id": "{placeholder.pk}"',
        ]

        for bit in expected_bits:
            self.assertIn(bit, content)

    def test_render_placeholder_toolbar_js_escaping(self):
        cms_page = create_page("page", 'nav_playground.html', "en")
        renderer = self.get_renderer()
        placeholder = cms_page.get_placeholders("en").get(slot='body')

        conf = {placeholder.slot: {'name': 'Content-with-dash'}}

        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            content = renderer.get_placeholder_toolbar_js(placeholder, cms_page)

        expected_bits = [
            '"MultiColumnPlugin"',
            '"addPluginHelpTitle": "Add plugin to placeholder \\"Content-with-dash\\""',
            '"name": "Content-with-dash"',
            f'"placeholder_id": "{placeholder.pk}"',
        ]

        for bit in expected_bits:
            self.assertIn(bit, content)


class TestContentRenderer(TestStructureRenderer):
    renderer_class = ContentRenderer

    @override_settings(CMS_PLACEHOLDER_CACHE=True)
    def test_placeholder_cache_enabled(self):
        cms_page = create_page("page", 'nav_playground.html', "en")
        request_path = cms_page.get_absolute_url('en')
        renderer = self.get_renderer(request_path, page=cms_page)
        self.assertTrue(renderer.placeholder_cache_is_enabled())

    @override_settings(CMS_PLACEHOLDER_CACHE=True)
    def test_placeholder_cache_disabled(self):
        with override_settings(CMS_PLACEHOLDER_CACHE=False):
            # Placeholder cache has been explicitly disabled
            renderer = self.get_renderer()
            self.assertFalse(renderer.placeholder_cache_is_enabled())

        with self.login_user_context(self.get_staff_user_with_no_permissions()):
            # Placeholder cache is disabled for all staff users
            renderer = self.get_renderer()
            self.assertFalse(renderer.placeholder_cache_is_enabled())

    def test_preload_placeholders_for_page_with_inherit_off(self):
        cms_page = create_page("page", 'nav_playground.html', "en")
        placeholder_1 = cms_page.get_placeholders("en").get(slot='body')
        placeholder_1_plugin_1 = add_plugin(
            placeholder_1,
            plugin_type='LinkPlugin',
            language='en',
            name='Link #1',
            external_link='https://www.django-cms.org',
        )
        placeholder_1_plugin_2 = add_plugin(
            placeholder_1,
            plugin_type='LinkPlugin',
            language='en',
            name='Link #2',
            external_link='https://www.django-cms.org',
        )
        placeholder_2 = cms_page.get_placeholders("en").get(slot='right-column')
        placeholder_2_plugin_1 = add_plugin(
            placeholder_2,
            plugin_type='LinkPlugin',
            language='en',
            name='Link #3',
            external_link='https://www.django-cms.org',
        )
        renderer = self.get_renderer(page=cms_page)
        renderer._preload_placeholders_for_page(cms_page)

        self.assertIn(cms_page.pk, renderer._placeholders_by_page_cache)
        self.assertIn(placeholder_1.slot, renderer._placeholders_by_page_cache[cms_page.pk])
        self.assertIn(placeholder_2.slot, renderer._placeholders_by_page_cache[cms_page.pk])

        cache = renderer._placeholders_by_page_cache[cms_page.pk]

        self.assertEqual(cache[placeholder_1.slot], placeholder_1)
        self.assertEqual(
            cache[placeholder_1.slot]._plugins_cache, deque([placeholder_1_plugin_1, placeholder_1_plugin_2])
        )
        self.assertEqual(cache[placeholder_2.slot], placeholder_2)
        self.assertEqual(cache[placeholder_2.slot]._plugins_cache, deque([placeholder_2_plugin_1]))

    def test_plugin_exception_catchers(self):
        """Tests if failing plugins do not break template rendering and report errors to the logger"""
        cms_page = create_page("page", 'nav_playground.html', "en")
        placeholder_1 = cms_page.get_placeholders("en").get(slot='body')
        add_plugin(
            placeholder_1,
            plugin_type='LinkPlugin',
            language='en',
            name='Link #1',
            external_link='https://www.django-cms.org',
        )
        add_plugin(
            placeholder_1,
            plugin_type='BuggyPlugin',
            language='en',
        )
        placeholder_2 = cms_page.get_placeholders("en").get(slot='right-column')
        placeholder_2_plugin_1 = add_plugin(
            placeholder_2,
            plugin_type='LinkPlugin',
            language='en',
            name='Link #3',
            external_link='https://www.django-cms.org',
        )
        renderer = self.get_renderer(page=cms_page)

        # Test if non-existent plugins creates error log and does not fail
        placeholder_2_plugin_1.plugin_type = 'NonExistingPlugin'
        placeholder_2_plugin_1.save()
        with self.assertLogs("cms.utils.plugins", level="ERROR") as logs:
            plugin_context = Context()
            renderer.render_placeholder(placeholder_2, plugin_context, "en")
            self.assertEqual(len(logs.output), 1)
            self.assertIn("Plugin not installed: NonExistingPlugin", logs.output[0])
        placeholder_2_plugin_1.plugin_type = 'LinkPlugin'
        placeholder_2_plugin_1.save()

        # Test if exception in template rendering creates error log and does not fail (plugin 1)
        # Test if exception in plugin.render creates error log and does not fail (plugin 2)
        # patch link plugin
        from cms.test_utils.project.pluginapp.plugins.link.cms_plugins import (
            LinkPlugin,
        )
        link_template = LinkPlugin.render_template
        LinkPlugin.render_template = "pluginapp/link/bugs.html"
        with self.assertLogs("cms.plugin_rendering", level="ERROR") as logs:
            plugin_context = Context()
            renderer.render_placeholder(placeholder_1, plugin_context, "en")
            self.assertEqual(len(logs.output), 2)
            self.assertIn("pluginapp/link/bugs.html", logs.output[0])
            self.assertIn("ZeroDivisionError:", logs.output[1])
        LinkPlugin.render_template = link_template


class TestLegacyRenderer(TestContentRenderer):
    renderer_class = LegacyRenderer
