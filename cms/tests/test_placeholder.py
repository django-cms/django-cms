from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, TemplateSyntaxError
from django.template.loader import get_template
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.encoding import force_str
from django.utils.numberformat import format
from sekizai.context import SekizaiContext

from cms import constants
from cms.api import add_plugin, create_page, create_title
from cms.exceptions import DuplicatePlaceholderWarning, PluginLimitReached
from cms.models.fields import PlaceholderField
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.test_utils.fixtures.fakemlng import FakemlngFixtures
from cms.test_utils.project.fakemlng.models import Translations
from cms.test_utils.project.placeholderapp.models import DynamicPlaceholderSlotExample, Example1, TwoPlaceholderExample
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase
from cms.test_utils.util.mock import AttributeObject
from cms.tests.test_toolbar import ToolbarTestBase
from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.placeholder import (
    MLNGPlaceholderActions,
    PlaceholderNoAction,
    _get_nodelist,
    _scan_placeholders,
    get_placeholder_conf,
    get_placeholders,
)
from cms.utils.plugins import assign_plugins, has_reached_plugin_limit
from cms.utils.urlutils import admin_reverse


def _get_placeholder_slots(template):
    return [pl.slot for pl in get_placeholders(template)]


def _render_placeholder(placeholder, context, **kwargs):
    request = context['request']
    toolbar = get_toolbar_from_request(request)
    content_renderer = toolbar.content_renderer
    return content_renderer.render_placeholder(placeholder, context, **kwargs)


class PlaceholderTestCase(TransactionCMSTestCase):
    def setUp(self):
        u = self._create_user("test", True, True)

        self._login_context = self.login_user_context(u)
        self._login_context.__enter__()

    def tearDown(self):
        self._login_context.__exit__(None, None, None)

    def test_placeholder_scanning_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_one.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'three']))

    def test_placeholder_scanning_variable_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_variable_extends.html')
        self.assertEqual(placeholders, ['one', 'two', 'three', 'four'])

    def test_placeholder_scanning_inherit_from_variable_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_inherit_from_variable_extends.html')
        self.assertEqual(placeholders, ['one', 'two', 'three', 'four'])

    def test_placeholder_scanning_sekizai_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_one_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'three']))

    def test_placeholder_scanning_include(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_two.html')
        self.assertEqual(sorted(placeholders), sorted(['child', 'three']))

    def test_placeholder_scanning_double_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_three.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'new_three']))

    def test_placeholder_scanning_sekizai_double_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_three_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'new_three']))

    def test_placeholder_scanning_complex(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_four.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'child', 'four']))

    def test_placeholder_scanning_super(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_five.html')
        self.assertEqual(sorted(placeholders), sorted(['one', 'extra_one', 'two', 'three']))

    def test_placeholder_scanning_nested(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_six.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'new_two', 'new_three']))

    def test_placeholder_scanning_duplicate(self):
        placeholders = self.assertWarns(
            DuplicatePlaceholderWarning,
            'Duplicate {% placeholder "one" %} in template placeholder_tests/test_seven.html.',
            _get_placeholder_slots, 'placeholder_tests/test_seven.html'
        )
        self.assertEqual(sorted(placeholders), sorted(['one']))

    def test_placeholder_scanning_extend_outside_block(self):
        placeholders = _get_placeholder_slots('placeholder_tests/outside.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'base_outside']))

    def test_placeholder_recursive_extend(self):
        placeholders = _get_placeholder_slots('placeholder_tests/recursive_extend.html')
        self.assertEqual(sorted(placeholders), sorted(['recursed_one', 'recursed_two', 'three']))

    def test_placeholder_scanning_sekizai_extend_outside_block(self):
        placeholders = _get_placeholder_slots('placeholder_tests/outside_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'base_outside']))

    def test_placeholder_scanning_extend_outside_block_nested(self):
        placeholders = _get_placeholder_slots('placeholder_tests/outside_nested.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'base_outside']))

    def test_placeholder_scanning_sekizai_extend_outside_block_nested(self):
        placeholders = _get_placeholder_slots('placeholder_tests/outside_nested_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted(['new_one', 'two', 'base_outside']))

    def test_placeholder_scanning_var(self):
        t = Template('{%load cms_tags %}{% include name %}{% placeholder "a_placeholder" %}')
        phs = sorted(node.get_declaration().slot for node in _scan_placeholders(t.nodelist))
        self.assertListEqual(phs, sorted(['a_placeholder']))

        t = Template('{% include "placeholder_tests/outside_nested_sekizai.html" %}')
        phs = sorted(node.get_declaration().slot for node in _scan_placeholders(t.nodelist))
        self.assertListEqual(phs, sorted(['two', 'new_one', 'base_outside']))

    def test_fieldsets_requests(self):
        response = self.client.get(admin_reverse('placeholderapp_example1_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(admin_reverse('placeholderapp_twoplaceholderexample_add'))
        self.assertEqual(response.status_code, 200)

    def test_page_only_plugins(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        response = self.client.get(admin_reverse('placeholderapp_example1_change', args=(ex.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'InheritPagePlaceholderPlugin')

    def test_inter_placeholder_plugin_move(self):
        ex = TwoPlaceholderExample(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        ph1 = ex.placeholder_1
        ph2 = ex.placeholder_2
        ph1_pl1 = add_plugin(ph1, 'TextPlugin', 'en', body='ph1 plugin1').cmsplugin_ptr
        ph1_pl2 = add_plugin(ph1, 'TextPlugin', 'en', body='ph1 plugin2').cmsplugin_ptr
        ph1_pl3 = add_plugin(ph1, 'TextPlugin', 'en', body='ph1 plugin3').cmsplugin_ptr
        ph2_pl1 = add_plugin(ph2, 'TextPlugin', 'en', body='ph2 plugin1').cmsplugin_ptr
        ph2_pl2 = add_plugin(ph2, 'TextPlugin', 'en', body='ph2 plugin2').cmsplugin_ptr
        ph2_pl3 = add_plugin(ph2, 'TextPlugin', 'en', body='ph2 plugin3').cmsplugin_ptr

        data = {
            'placeholder_id': str(ph2.pk),
            'plugin_id': str(ph1_pl2.pk),
            'target_language': 'en',
            'plugin_order[]': [str(p.pk) for p in [ph2_pl3, ph2_pl1, ph2_pl2, ph1_pl2]]
        }
        endpoint = self.get_move_plugin_uri(ph1_pl2, container=TwoPlaceholderExample)

        response = self.client.post(endpoint, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([ph1_pl1, ph1_pl3], list(ph1.cmsplugin_set.order_by('position')))
        self.assertEqual([ph2_pl3, ph2_pl1, ph2_pl2, ph1_pl2, ], list(ph2.cmsplugin_set.order_by('position')))

    def test_placeholder_render_ghost_plugin(self):
        """
        Tests a placeholder won't render a ghost plugin.
        """
        page_en = create_page('page_en', 'col_two.html', 'en')
        placeholder_en = page_en.placeholders.get(slot='col_left')

        CMSPlugin.objects.create(
            language='en',
            plugin_type='LinkPlugin',
            position=1,
            placeholder=placeholder_en,
            parent=None,
        )

        add_plugin(
            placeholder_en,
            "LinkPlugin",
            "en",
            name='name',
            external_link='http://example.com/',
        )

        context_en = SekizaiContext()
        context_en['request'] = self.get_request(language="en", page=page_en)

        content_en = _render_placeholder(placeholder_en, context_en)

        self.assertEqual(content_en.strip(), '<a href="http://example.com/">name</a>')

    def test_placeholder_render_ghost_plugin_with_child(self):
        """
        Tests a placeholder won't render a ghost plugin or any of it's children.
        """
        page_en = create_page('page_en', 'col_two.html', 'en')
        placeholder_en = page_en.placeholders.get(slot='col_left')

        plugin = CMSPlugin.objects.create(
            language='en',
            plugin_type='LinkPlugin',
            position=1,
            placeholder=placeholder_en,
            parent=None,
        )

        add_plugin(
            placeholder_en,
            "LinkPlugin",
            "en",
            target=plugin,
            name='invalid',
            external_link='http://example.com/',
        )

        add_plugin(
            placeholder_en,
            "LinkPlugin",
            "en",
            name='valid',
            external_link='http://example.com/',
        )

        context_en = SekizaiContext()
        context_en['request'] = self.get_request(language="en", page=page_en)

        content_en = _render_placeholder(placeholder_en, context_en)

        self.assertEqual(content_en.strip(), '<a href="http://example.com/">valid</a>')

    @override_settings(CMS_PERMISSION=False)
    def test_nested_plugin_escapejs(self):
        """
        Checks #1366 error condition.
        When adding/editing a plugin whose icon_src() method returns a URL
        containing an hyphen, the hyphen is escaped by django escapejs resulting
        in a incorrect URL
        """
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        ph1 = ex.placeholder
        #
        # add the test plugin
        #
        test_plugin = add_plugin(ph1, "EmptyPlugin", "en")
        test_plugin.save()
        endpoint = self.get_change_plugin_uri(test_plugin, container=Example1)
        response = self.client.post(endpoint, {})
        self.assertContains(response, "CMS.API.Helpers.onPluginSave")

    @override_settings(CMS_PERMISSION=False)
    def test_nested_plugin_escapejs_page(self):
        """
        Sibling test of the above, on a page.
        #1366 does not apply to placeholder defined in a page
        """
        page = create_page('page', 'col_two.html', 'en')
        ph1 = page.placeholders.get(slot='col_left')
        #
        # add the test plugin
        #
        test_plugin = add_plugin(ph1, "EmptyPlugin", "en")
        test_plugin.save()

        endpoint = self.get_change_plugin_uri(test_plugin)
        response = self.client.post(endpoint, {})
        self.assertContains(response, "CMS.API.Helpers.onPluginSave")

    def test_placeholder_scanning_fail(self):
        self.assertRaises(TemplateSyntaxError, _get_placeholder_slots, 'placeholder_tests/test_eleven.html')

    def test_placeholder_tag(self):
        request = self.get_request('/', language=settings.LANGUAGES[0][0])

        template = "{% load cms_tags %}{% render_placeholder placeholder %}"
        output = self.render_template_obj(template, {}, request)
        self.assertEqual(output, "")

        placeholder = Placeholder.objects.create(slot="test")
        output = self.render_template_obj(template, {'placeholder': placeholder}, request)
        self.assertEqual(output, "")
        self.assertEqual(placeholder.get_plugins().count(), 0)

        add_plugin(placeholder, "TextPlugin", settings.LANGUAGES[0][0], body="test")
        self.assertEqual(placeholder.get_plugins().count(), 1)
        placeholder = self.reload(placeholder)
        output = self.render_template_obj(template, {'placeholder': placeholder}, request)
        self.assertEqual(output, "test")

    def test_placeholder_tag_language(self):
        template = "{% load cms_tags %}{% render_placeholder placeholder language language %}"
        placeholder = Placeholder.objects.create(slot="test")
        add_plugin(placeholder, "TextPlugin", 'en', body="English")
        add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")
        request = self.get_request('/')

        output = self.render_template_obj(template, {'placeholder': placeholder, 'language': 'en'}, request)
        self.assertEqual(output.strip(), "English")

        del placeholder._plugins_cache

        output = self.render_template_obj(template, {'placeholder': placeholder, 'language': 'de'}, request)
        self.assertEqual(output.strip(), "Deutsch")

    def test_get_placeholder_conf(self):
        TEST_CONF = {
            'main': {
                'name': 'main content',
                'plugins': ['TextPlugin', 'LinkPlugin'],
                'default_plugins': [
                    {
                        'plugin_type': 'TextPlugin',
                        'values': {
                            'body': '<p>Some default text</p>'
                        },
                    },
                ],
            },
            'layout/home.html main': {
                'name': 'main content with FilerImagePlugin and limit',
                'plugins': ['TextPlugin', 'FilerImagePlugin', 'LinkPlugin'],
                'inherit': 'main',
                'limits': {'global': 1},
            },
            'layout/other.html main': {
                'name': 'main content with FilerImagePlugin and no limit',
                'inherit': 'layout/home.html main',
                'limits': {},
                'excluded_plugins': ['LinkPlugin']
            },
            None: {
                'name': 'All',
                'plugins': ['FilerImagePlugin', 'LinkPlugin'],
                'limits': {},
            },
        }

        with self.settings(CMS_PLACEHOLDER_CONF=TEST_CONF):
            # test no inheritance
            returned = get_placeholder_conf('plugins', 'main')
            self.assertEqual(returned, TEST_CONF['main']['plugins'])
            # test no inherited value with inheritance enabled
            returned = get_placeholder_conf('plugins', 'main', 'layout/home.html')
            self.assertEqual(returned, TEST_CONF['layout/home.html main']['plugins'])
            # test direct inherited value
            returned = get_placeholder_conf('plugins', 'main', 'layout/other.html')
            self.assertEqual(returned, TEST_CONF['layout/home.html main']['plugins'])
            # test excluded_plugins key
            returned = get_placeholder_conf('excluded_plugins', 'main', 'layout/other.html')
            self.assertEqual(returned, TEST_CONF['layout/other.html main']['excluded_plugins'])
            # test grandparent inherited value
            returned = get_placeholder_conf('default_plugins', 'main', 'layout/other.html')
            self.assertEqual(returned, TEST_CONF['main']['default_plugins'])
            # test generic configuration
            returned = get_placeholder_conf('plugins', 'something')
            self.assertEqual(returned, TEST_CONF[None]['plugins'])

    def test_placeholder_name_conf(self):
        page_en = create_page('page_en', 'col_two.html', 'en')
        placeholder_1 = page_en.placeholders.get(slot='col_left')
        placeholder_2 = Placeholder.objects.create(slot='col_left')
        placeholder_3 = Placeholder.objects.create(slot='no_name')

        TEST_CONF = {
            'col_left': {
                'name': 'renamed left column',
            },
            'col_two.html col_left': {
                'name': 'left column',
            },
            None: {
                'name': 'fallback',
            },
        }

        with self.settings(CMS_PLACEHOLDER_CONF=TEST_CONF):
            self.assertEqual(force_str(placeholder_1.get_label()), 'left column')
            self.assertEqual(force_str(placeholder_2.get_label()), 'renamed left column')
            self.assertEqual(force_str(placeholder_3.get_label()), 'fallback')

        del TEST_CONF[None]

        with self.settings(CMS_PLACEHOLDER_CONF=TEST_CONF):
            self.assertEqual(force_str(placeholder_1.get_label()), 'left column')
            self.assertEqual(force_str(placeholder_2.get_label()), 'renamed left column')
            self.assertEqual(force_str(placeholder_3.get_label()), 'No_Name')

    def test_placeholders_from_blocks_order(self):
        placeholders = _get_placeholder_slots('placeholder_tests/test_with_block.html')
        self.assertEqual(placeholders, ['one', 'two', 'three', 'four'])

    def test_placeholder_scanning_nested_super(self):
        placeholders = _get_placeholder_slots('placeholder_tests/nested_super_level1.html')
        self.assertEqual(sorted(placeholders), sorted(['level1', 'level2', 'level3', 'level4']))

    def test_placeholder_field_no_related_name(self):
        self.assertRaises(ValueError, PlaceholderField, 'placeholder', related_name='+')

    def test_placeholder_field_db_table(self):
        """
        Test for leaking Model._meta.db_table monkeypatching on SQLite (#3891).
        """
        example = Category.objects.create(
            name='category',
            parent=None, depth=1,
        )
        self.assertEqual(example.description._get_attached_fields()[0].model, Category)
        self.assertEqual(len(example.description._get_attached_fields()), 1)

    def test_placeholder_field_valid_slotname(self):
        self.assertRaises(ImproperlyConfigured, PlaceholderField, 10)

    def test_placeholder_field_dynamic_slot_generation(self):
        instance = DynamicPlaceholderSlotExample.objects.create(char_1='slot1', char_2='slot2')
        self.assertEqual(instance.char_1, instance.placeholder_1.slot)
        self.assertEqual(instance.char_2, instance.placeholder_2.slot)

    def test_placeholder_field_dynamic_slot_update(self):
        instance = DynamicPlaceholderSlotExample.objects.create(char_1='slot1', char_2='slot2')

        # Plugin counts
        old_placeholder_1_plugin_count = len(instance.placeholder_1.get_plugins())
        old_placeholder_2_plugin_count = len(instance.placeholder_2.get_plugins())

        # Switch around the slot names
        instance.char_1, instance.char_2 = instance.char_2, instance.char_1

        # Store the ids before save, to test that a new placeholder is NOT created.
        placeholder_1_id = instance.placeholder_1.pk
        placeholder_2_id = instance.placeholder_2.pk

        # Save instance
        instance.save()

        current_placeholder_1_plugin_count = len(instance.placeholder_1.get_plugins())
        current_placeholder_2_plugin_count = len(instance.placeholder_2.get_plugins())

        # Now test that the placeholder slots have changed
        self.assertEqual(instance.char_2, 'slot1')
        self.assertEqual(instance.char_1, 'slot2')
        # Test that a new placeholder was never created
        self.assertEqual(instance.placeholder_1.pk, placeholder_1_id)
        self.assertEqual(instance.placeholder_2.pk, placeholder_2_id)
        # And test the plugin counts remain the same
        self.assertEqual(old_placeholder_1_plugin_count, current_placeholder_1_plugin_count)
        self.assertEqual(old_placeholder_2_plugin_count, current_placeholder_2_plugin_count)

    def test_plugins_language_fallback(self):
        """ Tests language_fallback placeholder configuration """
        page_en = create_page('page_en', 'col_two.html', 'en')
        title_de = create_title("de", "page_de", page_en)
        placeholder_en = page_en.placeholders.get(slot='col_left')
        placeholder_de = title_de.page.placeholders.get(slot='col_left')
        add_plugin(placeholder_en, 'TextPlugin', 'en', body='en body')

        context_en = SekizaiContext()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_de = SekizaiContext()
        context_de['request'] = self.get_request(language="de", page=page_en)

        # First test the default (fallback) behavior)
        # English page should have the text plugin
        content_en = _render_placeholder(placeholder_en, context_en)
        self.assertRegex(content_en, "^en body$")

        # Deutsch page have text due to fallback
        content_de = _render_placeholder(placeholder_de, context_de)
        self.assertRegex(content_de, "^en body$")
        self.assertEqual(len(content_de), 7)

        conf = {
            'col_left': {
                'language_fallback': False,
            },
        }
        # configure non fallback
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            # Deutsch page should have no text
            del placeholder_de._plugins_cache
            cache.clear()
            content_de = _render_placeholder(placeholder_de, context_de)
            # Deutsch page should inherit english content
            self.assertNotRegex(content_de, "^en body$")
            context_de2 = SekizaiContext()
            request = self.get_request(language="de", page=page_en)
            request.session['cms_edit'] = True
            request.user = self.get_superuser()
            request.toolbar = CMSToolbar(request)
            context_de2['request'] = request
            del placeholder_de._plugins_cache
            cache.clear()
            content_de2 = _render_placeholder(placeholder_de, context_de2)
            self.assertFalse("en body" in content_de2)
            # remove the cached plugins instances
            del placeholder_de._plugins_cache
            cache.clear()
            # Then we add a plugin to check for proper rendering
            add_plugin(placeholder_de, 'TextPlugin', 'de', body='de body')
            content_de = _render_placeholder(placeholder_de, context_de)
            self.assertRegex(content_de, "^de body$")

    def test_nested_plugins_language_fallback(self):
        """ Tests language_fallback placeholder configuration for nested plugins"""
        page_en = create_page('page_en', 'col_two.html', 'en')
        title_de = create_title("de", "page_de", page_en)
        placeholder_en = page_en.placeholders.get(slot='col_left')
        placeholder_de = title_de.page.placeholders.get(slot='col_left')
        link_en = add_plugin(placeholder_en, 'LinkPlugin', 'en', name='en name', external_link='http://example.com/en')
        add_plugin(placeholder_en, 'TextPlugin', 'en',  target=link_en, body='en body')

        context_en = SekizaiContext()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_de = SekizaiContext()
        context_de['request'] = self.get_request(language="de", page=page_en)

        conf = {
            'col_left': {
                'language_fallback': True,
            },
        }
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            content_de = _render_placeholder(placeholder_de, context_de)
            self.assertRegex(content_de, "<a href=\"http://example.com/en\"")
            self.assertRegex(content_de, "en body")
            context_de2 = SekizaiContext()
            request = self.get_request(language="de", page=page_en)
            request.session['cms_edit'] = True
            request.user = self.get_superuser()
            request.toolbar = CMSToolbar(request)
            context_de2['request'] = request
            del placeholder_de._plugins_cache
            cache.clear()
            content_de2 = _render_placeholder(placeholder_de, context_de2)
            self.assertFalse("en body" in content_de2)
            # remove the cached plugins instances
            del placeholder_de._plugins_cache
            cache.clear()
            # Then we add a plugin to check for proper rendering
            link_de = add_plugin(
                placeholder_en,
                'LinkPlugin',
                language='de',
                name='de name',
                external_link='http://example.com/de',
            )
            add_plugin(placeholder_en, 'TextPlugin', 'de',  target=link_de, body='de body')
            content_de = _render_placeholder(placeholder_de, context_de)
            self.assertRegex(content_de, "<a href=\"http://example.com/de\"")
            self.assertRegex(content_de, "de body")

    def test_plugins_non_default_language_fallback(self):
        """ Tests language_fallback placeholder configuration """
        page_en = create_page('page_en', 'col_two.html', 'en')
        create_title("de", "page_de", page_en)
        placeholder_en = page_en.placeholders.get(slot='col_left')
        placeholder_de = page_en.placeholders.get(slot='col_left')
        add_plugin(placeholder_de, 'TextPlugin', 'de', body='de body')

        context_en = SekizaiContext()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_de = SekizaiContext()
        context_de['request'] = self.get_request(language="de", page=page_en)

        # First test the default (fallback) behavior)
        # Deutsch page should have the text plugin
        content_de = _render_placeholder(placeholder_en, context_de)
        self.assertRegexpMatches(content_de, "^de body$")
        del placeholder_en._plugins_cache
        cache.clear()
        # English page should have no text
        content_en = _render_placeholder(placeholder_en, context_en)
        self.assertRegex(content_en, "^de body$")
        self.assertEqual(len(content_en), 7)
        del placeholder_en._plugins_cache
        cache.clear()
        conf = {
            'col_left': {
                'language_fallback': False,
            },
        }
        # configure non-fallback
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            # English page should have deutsch text
            content_en = _render_placeholder(placeholder_en, context_en)
            self.assertNotRegex(content_en, "^de body$")

            # remove the cached plugins instances
            del placeholder_en._plugins_cache
            cache.clear()
            # Then we add a plugin to check for proper rendering
            add_plugin(placeholder_en, 'TextPlugin', 'en', body='en body')
            content_en = _render_placeholder(placeholder_en, context_en)
            self.assertRegex(content_en, "^en body$")

    def test_plugins_discarded_with_language_fallback(self):
        """
        Tests side effect of language fallback: if fallback enabled placeholder
        existed, it discards all other existing plugins
        """
        page_en = create_page('page_en', 'col_two.html', 'en')
        create_title("de", "page_de", page_en)
        placeholder_sidebar_en = page_en.placeholders.get(slot='col_sidebar')
        placeholder_en = page_en.placeholders.get(slot='col_left')
        add_plugin(placeholder_sidebar_en, 'TextPlugin', 'en', body='en body')

        context_en = SekizaiContext()
        context_en['request'] = self.get_request(language="en", page=page_en)

        conf = {
            'col_left': {
                'language_fallback': True,
            },
        }
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            # call assign plugins first, as this is what is done in real cms life
            # for all placeholders in a page at once
            assign_plugins(context_en['request'],
                           [placeholder_sidebar_en, placeholder_en], 'col_two.html')
            # if the normal, non fallback enabled placeholder still has content
            content_en = _render_placeholder(placeholder_sidebar_en, context_en)
            self.assertRegex(content_en, "^en body$")

            # remove the cached plugins instances
            del placeholder_sidebar_en._plugins_cache
            cache.clear()

    def test_plugins_prepopulate(self):
        """ Tests prepopulate placeholder configuration """

        conf = {
            'col_left': {
                'default_plugins' : [
                    {
                        'plugin_type':'TextPlugin',
                        'values':{'body':'<p>en default body 1</p>'},
                    },
                    {
                        'plugin_type':'TextPlugin',
                        'values':{'body':'<p>en default body 2</p>'},
                    },
                ]
            },
        }
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            page = create_page('page_en', 'col_two.html', 'en')
            placeholder = page.placeholders.get(slot='col_left')
            context = SekizaiContext()
            context['request'] = self.get_request(language="en", page=page)
            # Our page should have "en default body 1" AND "en default body 2"
            content = _render_placeholder(placeholder, context)
            self.assertRegex(content, r"^<p>en default body 1</p>\s*<p>en default body 2</p>$")

    def test_plugins_children_prepopulate(self):
        """
        Validate a default textplugin with a nested default link plugin
        """

        conf = {
            'col_left': {
                'default_plugins': [
                    {
                        'plugin_type': 'TextPlugin',
                        'values': {
                            'body': '<p>body %(_tag_child_1)s and %(_tag_child_2)s</p>'
                        },
                        'children': [
                            {
                                'plugin_type': 'LinkPlugin',
                                'values': {
                                    'name': 'django',
                                    'external_link': 'https://www.djangoproject.com/'
                                },
                            },
                            {
                                'plugin_type': 'LinkPlugin',
                                'values': {
                                    'name': 'django-cms',
                                    'external_link': 'https://www.django-cms.org'
                                },
                            },
                        ]
                    },
                ]
            },
        }

        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            page = create_page('page_en', 'col_two.html', 'en')
            placeholder = page.placeholders.get(slot='col_left')
            context = SekizaiContext()
            context['request'] = self.get_request(language="en", page=page)
            _render_placeholder(placeholder, context)
            plugins = placeholder.get_plugins_list()
            self.assertEqual(len(plugins), 3)
            self.assertEqual(plugins[0].plugin_type, 'TextPlugin')
            self.assertEqual(plugins[1].plugin_type, 'LinkPlugin')
            self.assertEqual(plugins[2].plugin_type, 'LinkPlugin')
            self.assertTrue(plugins[1].parent == plugins[2].parent and plugins[1].parent == plugins[0])

    def test_placeholder_pk_thousands_format(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        for placeholder in page.placeholders.all():
            page.placeholders.remove(placeholder)
            placeholder.pk += 1000
            placeholder.save()
            page.placeholders.add(placeholder)
        page.reload()
        for placeholder in page.placeholders.all():
            add_plugin(placeholder, "TextPlugin", "en", body="body")
        with self.settings(USE_THOUSAND_SEPARATOR=True, USE_L10N=True):
            # Superuser
            user = self.get_superuser()
            self.client.login(username=getattr(user, get_user_model().USERNAME_FIELD),
                              password=getattr(user, get_user_model().USERNAME_FIELD))
            endpoint = page.get_absolute_url() + '?' + get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
            response = self.client.get(endpoint)
            for placeholder in page.placeholders.all():
                self.assertContains(
                    response, '"placeholder_id": "%s"' % placeholder.pk)
                self.assertNotContains(
                    response, '"placeholder_id": "%s"' % format(
                        placeholder.pk, ".", grouping=3, thousand_sep=","))
                self.assertNotContains(
                    response, '"plugin_id": "%s"' % format(
                        placeholder.pk, ".", grouping=3, thousand_sep=","))
                self.assertNotContains(
                    response, '"clipboard": "%s"' % format(
                        response.context['request'].toolbar.clipboard.pk, ".",
                        grouping=3, thousand_sep=","))

    def test_placeholder_languages_model(self):
        """
        Checks the retrieval of filled languages for a placeholder in a django
        model
        """
        avail_langs = {'en', 'de', 'fr'}
        # Setup instance
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        #
        # add the test plugin
        #
        for lang in avail_langs:
            add_plugin(ex.placeholder, "EmptyPlugin", lang)
        # reload instance from database
        ex = Example1.objects.get(pk=ex.pk)
        # get languages
        langs = [lang['code'] for lang in ex.placeholder.get_filled_languages()]
        self.assertEqual(avail_langs, set(langs))

    def test_placeholder_languages_page(self):
        """
        Checks the retrieval of filled languages for a placeholder in a django
        model
        """
        avail_langs = {'en', 'de', 'fr'}
        # Setup instances
        page = create_page('test page', 'col_two.html', 'en')
        for lang in avail_langs:
            if lang != 'en':
                create_title(lang, 'test page %s' % lang, page)
        placeholder = page.placeholders.get(slot='col_sidebar')
        #
        # add the test plugin
        #
        for lang in avail_langs:
            add_plugin(placeholder, "EmptyPlugin", lang)
        # reload placeholder from database
        placeholder = page.placeholders.get(slot='col_sidebar')
        # get languages
        langs = [lang['code'] for lang in placeholder.get_filled_languages()]
        self.assertEqual(avail_langs, set(langs))

    @override_settings(TEMPLATE_LOADERS=(
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),))
    def test_cached_template_not_corrupted_by_placeholder_scan(self):
        """
        This is the test for the low-level code that caused the bug:
        the placeholder scan corrupts the nodelist of the extends node,
        which is retained by the cached template loader, and future
        renders of that template will render the super block twice.
        """

        nodelist = _get_nodelist(get_template("placeholder_tests/test_super_extends_2.html"))
        self.assertNotIn(
            'one',
            nodelist[0].blocks.keys(),
            "test_super_extends_1.html contains a block called 'one', "
            "but _2.html does not."
        )

        _get_placeholder_slots("placeholder_tests/test_super_extends_2.html")

        nodelist = _get_nodelist(get_template("placeholder_tests/test_super_extends_2.html"))
        self.assertNotIn(
            'one',
            nodelist[0].blocks.keys(),
            "test_super_extends_1.html still should not contain a block "
            "called 'one' after rescanning placeholders."
        )

    @override_settings(TEMPLATE_LOADERS=(
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),))
    def test_super_extends_not_corrupted_by_placeholder_scan(self):
        """
        This is the test for the symptom of the bug: because the block
        context now contains two copies of the inherited block, that block
        will be executed twice, and if it adds content to {{block.super}},
        that content will be added twice.
        """
        template = get_template("placeholder_tests/test_super_extends_2.html")
        output = template.render({})
        self.assertEqual(
            ['Whee'], [o for o in output.split('\n') if 'Whee' in o]
        )

        _get_placeholder_slots("placeholder_tests/test_super_extends_2.html")

        template = get_template("placeholder_tests/test_super_extends_2.html")
        output = template.render({})
        self.assertEqual(
            ['Whee'], [o for o in output.split('\n') if 'Whee' in o]
        )


class PlaceholderActionTests(FakemlngFixtures, CMSTestCase):
    def test_placeholder_no_action(self):
        actions = PlaceholderNoAction()
        self.assertEqual(actions.get_copy_languages(), [])
        self.assertFalse(actions.copy())

    def test_mlng_placeholder_actions_get_copy_languages(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        en = Translations.objects.get(language_code='en')
        fieldname = 'placeholder'
        fr_copy_languages = actions.get_copy_languages(
            fr.placeholder, Translations, fieldname
        )
        de_copy_languages = actions.get_copy_languages(
            de.placeholder, Translations, fieldname
        )
        en_copy_languages = actions.get_copy_languages(
            en.placeholder, Translations, fieldname
        )
        EN = ('en', 'English')
        FR = ('fr', 'French')
        self.assertEqual(set(fr_copy_languages), {EN})
        self.assertEqual(set(de_copy_languages), {EN, FR})
        self.assertEqual(set(en_copy_languages), {FR})

    def test_mlng_placeholder_actions_copy(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        self.assertEqual(fr.placeholder.get_plugins().count(), 1)
        self.assertEqual(de.placeholder.get_plugins().count(), 0)

        new_plugins = actions.copy(de.placeholder, 'fr', 'placeholder', Translations, 'de')
        self.assertEqual(len(new_plugins), 1)

        de = self.reload(de)
        fr = self.reload(fr)

        self.assertEqual(fr.placeholder.get_plugins().count(), 1)
        self.assertEqual(de.placeholder.get_plugins().count(), 1)

    def test_mlng_placeholder_actions_empty_copy(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        self.assertEqual(fr.placeholder.get_plugins().count(), 1)
        self.assertEqual(de.placeholder.get_plugins().count(), 0)

        new_plugins = actions.copy(fr.placeholder, 'de', 'placeholder', Translations, 'fr')
        self.assertEqual(len(new_plugins), 0)

        de = self.reload(de)
        fr = self.reload(fr)

        self.assertEqual(fr.placeholder.get_plugins().count(), 1)
        self.assertEqual(de.placeholder.get_plugins().count(), 0)

    def test_mlng_placeholder_actions_no_placeholder(self):
        actions = MLNGPlaceholderActions()
        Translations.objects.filter(language_code='nl').update(placeholder=None)
        de = Translations.objects.get(language_code='de')
        nl = Translations.objects.get(language_code='nl')
        self.assertEqual(nl.placeholder, None)
        self.assertEqual(de.placeholder.get_plugins().count(), 0)

        okay = actions.copy(de.placeholder, 'nl', 'placeholder', Translations, 'de')
        self.assertEqual(okay, False)

        de = self.reload(de)
        nl = self.reload(nl)

        nl = Translations.objects.get(language_code='nl')
        de = Translations.objects.get(language_code='de')


@override_settings(CMS_PERMISSION=False)
class PlaceholderModelTests(ToolbarTestBase, CMSTestCase):
    def get_mock_user(self, superuser):
        return AttributeObject(
            is_superuser=superuser,
            has_perm=lambda string: False,
        )

    def get_mock_request(self, superuser=True):
        return AttributeObject(
            superuser=superuser,
            user=self.get_mock_user(superuser)
        )

    def test_check_placeholder_permissions_ok_for_superuser(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        user = self.get_mock_user(True)
        result = ph.has_change_permission(user)
        self.assertTrue(result)

    def test_check_placeholder_permissions_nok_for_user(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        user = self.get_mock_user(False)
        result = ph.has_change_permission(user)
        self.assertFalse(result)

    def test_check_unicode_rendering(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = force_str(ph)
        self.assertEqual(result, 'test')

    def test_excercise_get_attached_model(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph._get_attached_model()
        self.assertEqual(result, None) # Simple PH - no model

    def test_excercise_get_attached_field_name(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph._get_attached_field_name()
        self.assertEqual(result, None) # Simple PH - no field name

    def test_excercise_get_attached_models_notplugins(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        ph = ex.placeholder
        result = list(ph._get_attached_models())
        self.assertEqual(result, [Example1]) # Simple PH - Example1 model
        add_plugin(ph, 'TextPlugin', 'en', body='en body')
        result = list(ph._get_attached_models())
        self.assertEqual(result, [Example1]) # Simple PH still one Example1 model

    def test_excercise_get_attached_fields_notplugins(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four',
        )
        ex.save()
        ph = ex.placeholder
        result = [f.name for f in list(ph._get_attached_fields())]
        self.assertEqual(result, ['placeholder']) # Simple PH - placeholder field name
        add_plugin(ph, 'TextPlugin', 'en', body='en body')
        result = [f.name for f in list(ph._get_attached_fields())]
        self.assertEqual(result, ['placeholder']) # Simple PH - still one placeholder field name

    def test_repr(self):
        unsaved_ph = Placeholder()
        self.assertIn('id=None', repr(unsaved_ph))
        self.assertIn("slot=''", repr(unsaved_ph))

        saved_ph = Placeholder.objects.create(slot='test')
        self.assertIn(f'id={saved_ph.pk}', repr(saved_ph))
        self.assertIn(f"slot='{saved_ph.slot}'", repr(saved_ph))


class PlaceholderConfTests(TestCase):
    def test_get_all_plugins_single_page(self):
        page = create_page('page', 'col_two.html', 'en')
        placeholder = page.placeholders.get(slot='col_left')
        conf = {
            'col_two': {
                'plugins': ['TextPlugin', 'LinkPlugin'],
            },
            'col_two.html col_left': {
                'plugins': ['LinkPlugin'],
            },
        }
        LinkPlugin = plugin_pool.get_plugin('LinkPlugin')
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            plugins = plugin_pool.get_all_plugins(placeholder, page)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(plugins[0], LinkPlugin)

    def test_get_all_plugins_inherit(self):
        parent = create_page('parent', 'col_two.html', 'en')
        page = create_page('page', constants.TEMPLATE_INHERITANCE_MAGIC, 'en', parent=parent)
        placeholder = page.placeholders.get(slot='col_left')
        conf = {
            'col_two': {
                'plugins': ['TextPlugin', 'LinkPlugin'],
            },
            'col_two.html col_left': {
                'plugins': ['LinkPlugin'],
            },
        }
        LinkPlugin = plugin_pool.get_plugin('LinkPlugin')
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            plugins = plugin_pool.get_all_plugins(placeholder, page)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(plugins[0], LinkPlugin)

    def test_plugins_limit_global(self):
        """ Tests placeholder limit configuration for nested plugins"""
        page = create_page('page', 'col_two.html', 'en')
        placeholder = page.placeholders.get(slot='col_left')
        conf = {
            'col_left': {
                'limits': {
                    'global': 1,
                },
            },
        }
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            add_plugin(placeholder, 'LinkPlugin', 'en', name='name', external_link='http://example.com/en')
            self.assertRaises(
                PluginLimitReached, has_reached_plugin_limit, placeholder=placeholder, plugin_type='LinkPlugin',
                language='en', template=None, parent_plugin=None
            )

    def test_plugins_limit_global_children(self):
        """ Tests placeholder limit configuration for nested plugins"""
        page = create_page('page', 'col_two.html', 'en')
        placeholder = page.placeholders.get(slot='col_left')
        conf = {
            'col_left': {
                'limits': {
                    'global_children': 1,
                },
            },
        }
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            link = add_plugin(placeholder, 'LinkPlugin', 'en', name='name', external_link='http://example.com/en')
            add_plugin(placeholder, 'TextPlugin', 'en', target=link)
            add_plugin(placeholder, 'TextPlugin', 'en', target=link)
            self.assertRaises(
                PluginLimitReached, has_reached_plugin_limit, placeholder=placeholder, plugin_type='LinkPlugin',
                language='en', template=None, parent_plugin=None
            )
