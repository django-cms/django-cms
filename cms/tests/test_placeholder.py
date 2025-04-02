from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, TemplateSyntaxError
from django.template.loader import get_template
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.encoding import force_str
from django.utils.numberformat import format
from sekizai.context import SekizaiContext

from cms import constants
from cms.api import add_plugin, create_page, create_page_content
from cms.exceptions import DuplicatePlaceholderWarning, PlaceholderNotFound
from cms.models.fields import PlaceholderField
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.settingmodels import UserSettings
from cms.plugin_pool import plugin_pool
from cms.test_utils.fixtures.fakemlng import FakemlngFixtures
from cms.test_utils.project.fakemlng.models import Translations
from cms.test_utils.project.placeholder_relation_field_app.models import (
    FancyPoll,
)
from cms.test_utils.project.placeholderapp.models import (
    DynamicPlaceholderSlotExample,
    Example1,
    TwoPlaceholderExample,
)
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase
from cms.test_utils.util.mock import AttributeObject
from cms.tests.test_toolbar import ToolbarTestBase
from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_structure_url,
    get_toolbar_from_request,
)
from cms.utils.placeholder import (
    MLNGPlaceholderActions,
    PlaceholderNoAction,
    _get_nodelist,
    _scan_placeholders,
    get_placeholder_conf,
    get_placeholders,
)
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

    def test_placeholder_scanning_no_object(self):
        """Placeholder scanning for a template without a toolbar object raises PlaceholderNotFound"""

        context = SekizaiContext()
        request = self.get_request(language="en", page=None)
        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()
        with self.assertRaises(PlaceholderNotFound):
            renderer.render_obj_placeholder("someslot", context, False)


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

        endpoint = self.get_move_plugin_uri(ph1_pl2)

        # Move ph2_pl3 to position 1 on placeholder 2
        data = {
            'plugin_id': str(ph2_pl3.pk),
            'target_language': 'en',
            'target_position': 1,
        }

        response = self.client.post(endpoint, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([ph2_pl3, ph2_pl1, ph2_pl2], list(ph2.cmsplugin_set.order_by('position')))

        # Move ph1_pl2 to last position on placeholder 2
        data = {
            'placeholder_id': str(ph2.pk),
            'plugin_id': str(ph1_pl2.pk),
            'target_language': 'en',
            'target_position': ph2.get_next_plugin_position('en', insert_order='last'),
        }

        response = self.client.post(endpoint, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([ph1_pl1, ph1_pl3], list(ph1.cmsplugin_set.order_by('position')))
        self.assertEqual([ph2_pl3, ph2_pl1, ph2_pl2, ph1_pl2], list(ph2.cmsplugin_set.order_by('position')))

    def test_inter_placeholder_nested_plugin_move(self):
        # Specific test to move a large number of plugins from one placeholder to a placeholder with a
        # small number of plugins, between similarly size placeholders and a small number of plugins to
        # a placeholder with a large number of plugins (For this test large is 10 times small.)
        # These cases ensure the move operation is flexible with the relation of plugins, e.g. creates enough space
        #
        # To ensure the test works with different languages, plugins are created for a number of language with
        # interlacing pk, the move operation only happens in the first language - others should stay unchanged.
        #
        language_fun = ('en', 'de', 'it', 'de-formal')
        # symmetric and asymmetric plugin numbers in target placeholder, source placeholder
        # (1, 10) One plugin in the target placeholder, 10 plugins to be moved
        # (5, 5) Same size situation
        # (10, 1) Ten plugins in the target placeholder, 1 plugin to be moved
        for n1, n2 in ((1, 10), (10, 1), (5, 5)):
            ex = TwoPlaceholderExample()
            ex.save()
            ph1 = ex.placeholder_1
            ph2 = ex.placeholder_2
            ph1parent = {}  # parents
            ph2parent = {}
            ph1children = {}  # Children
            ph2children = {}
            for lang in language_fun:
                # first create parent in target placeholder
                ph1parent[lang] = add_plugin(ph1, 'TextPlugin', lang, body='ph1 parent').cmsplugin_ptr
                ph1children[lang] = []
                for i in range(n1):
                    # create children in target placeholder
                    ph1children[lang].append(
                        add_plugin(ph1, 'TextPlugin', lang, target=ph1parent[lang], body=f'ph1 child{i}').cmsplugin_ptr
                    )
                # now create parent in source placeholder
                ph2parent[lang] = add_plugin(ph2, 'TextPlugin', lang, body='ph2 parent').cmsplugin_ptr
                ph2children[lang] = []
                for i in range(n2):
                    # followed by children in source placeholder
                    ph2children[lang].append(
                        add_plugin(ph2, 'TextPlugin', lang, target=ph2parent[lang], body=f'ph2 child{i}').cmsplugin_ptr
                    )
            # Plugins have been created in all languages. Now move the first language plugins from the source
            # placeholder to the target placeholder
            ph2.move_plugin(
                ph2parent[language_fun[0]],  # Move parent (first language only) **and** its children
                target_plugin=ph1parent[language_fun[0]],  # as child of parent in target placeholder
                target_position=2,  # First child, that is
                target_placeholder=ph1,
            )
            # The result in theory:
            # Parent Target Placeholder
            #   Parent Source Placeholder         <-- Moved plugin parent
            #     Children Source Placeholder     <-- Moved plugin children
            #   Children Target Placeholder
            left = (
                [ph1parent[language_fun[0]], ph2parent[language_fun[0]]]
                + ph2children[language_fun[0]] + ph1children[language_fun[0]]
            )
            # The result in practice
            right = list(ph1.cmsplugin_set.filter(language=language_fun[0]).order_by('position'))
            self.assertEqual(left, right)

            ph1.delete()
            ph2.delete()

    def test_get_last_plugin_position(self):
        # get_last_plugin_position is supposed to either get the position of the last plugin of the placeholder
        # or the position of the last grand(!) child if a given plugin, independent of language!
        # This test creates a tree of the form

        # 1. Plugin 1
        # 2.   Plugin 2
        # 3.     Plugin 3
        # 4.       Plugin 4
        # 5. Final Plugin

        language_fun = ('en', 'de', 'it', 'de-formal')

        ex = Example1()
        ex.save()
        ph = ex.placeholder

        parent = None
        n = 4  # This will be the position of the last plugin

        plugins = {lang: [] for lang in language_fun}
        parent = dict.fromkeys(language_fun)
        for i in range(n):
            for lang in language_fun:
                parent[lang] = add_plugin(ph, 'TextPlugin', lang, target=parent[lang]).cmsplugin_ptr
                plugins[lang].append(parent[lang])

        for lang in language_fun:
            self.assertEqual(ph.get_last_plugin_position(lang), n)  # should be n

            for parent in plugins[lang]:
                # needs to be n also if we look at the parents
                # the last plugin does not have a child hence position should be none
                self.assertEqual(
                    ph.get_last_plugin_position(lang, parent=parent),
                    n if parent != plugins[lang][-1] else None,
                )

            add_plugin(ph, 'TextPlugin', lang, target=None)  # Add a top level final plugin

            self.assertEqual(ph.get_last_plugin_position(lang), n + 1)  # plus the last plugin
            for parent in plugins[lang]:
                # still needs to be n also if we look at the parents
                # the last plugin does not have a child hence position should be none
                self.assertEqual(
                    ph.get_last_plugin_position(lang, parent=parent),
                    n if parent != plugins[lang][-1] else None,
                )

    def test_get_last_plugin_position_order(self):
        # This test creates a tree like this
        # 1. Plugin n
        # 2. Plugin n-1
        # 3. Plugin n-2
        #    ...
        # n. Plugin 1
        # The children are created with the 'first-child' option, i.e. in reverse order: new children
        # are prepended to the existing ones. Still get_last_plugin_position needs to return the position
        # n if the last plugin (though it was created first).
        # To make this more fun we interlace plugins with other languages to ensure they do not influence
        # the result.
        language_fun = ('en', 'de', 'it', 'en-US')
        ex = Example1()
        ex.save()
        ph = ex.placeholder

        n = 15  # This will be the position of the last plugin

        for i in range(n):
            # Use 'first-child' order causes pk and position run inversely
            for language in language_fun:
                add_plugin(ph, 'TextPlugin', language, 'first-child').cmsplugin_ptr

        self.assertEqual(ph.get_last_plugin_position('en'), n)  # should be n

    def test_copy_plugin(self):
        superuser = self.get_superuser()
        page_en = create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        ph_source = page_en.get_placeholders('en').get(slot="body")
        plugin = add_plugin(ph_source, "LinkPlugin", "en", name="A Link", external_link="https://www.django-cms.org")
        endpoint = self.get_copy_plugin_uri(plugin)
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': ph_source.pk,
            'source_language': plugin.language,
            'target_language': 'en',
            'target_placeholder_id': user_settings.clipboard.pk,
        }

        with self.login_user_context(superuser):
            # Copy plugins into the clipboard
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

        clipboard_plugins = user_settings.clipboard.get_plugins()
        self.assertTrue(clipboard_plugins.filter(plugin_type='LinkPlugin').exists())
        self.assertEqual(len(clipboard_plugins), 1)

    def test_copy_plugin_without_custom_model(self):
        superuser = self.get_superuser()
        page_en = create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        ph_source = page_en.get_placeholders('en').get(slot="body")
        plugin = add_plugin(ph_source, "NoCustomModel", "en")
        endpoint = self.get_copy_plugin_uri(plugin)
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': ph_source.pk,
            'source_language': plugin.language,
            'target_language': 'en',
            'target_placeholder_id': user_settings.clipboard.pk,
        }

        with self.login_user_context(superuser):
            # Copy plugins into the clipboard
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

        clipboard_plugins = user_settings.clipboard.get_plugins()
        self.assertTrue(clipboard_plugins.filter(plugin_type='NoCustomModel').exists())
        self.assertEqual(len(clipboard_plugins), 1)

    def test_paste_plugin_from_clipboard(self):
        superuser = self.get_superuser()
        page_en = create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        ph_target = page_en.get_placeholders('en').get(slot="body")
        add_plugin(ph_target, "LinkPlugin", "en", name="A Link", external_link="https://www.django-cms.org")
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        plugin = add_plugin(
            user_settings.clipboard,
            "LinkPlugin",
            language="en",
            name="A Link",
            external_link="https://www.django-cms.org",
        )
        endpoint = self.get_move_plugin_uri(plugin)

        # Paste LinkPlugin to first position
        data = {
            'plugin_id': plugin.pk,
            'move_a_copy': True,
            'target_language': 'en',
            'target_position': 1,
            'placeholder_id': ph_target.pk,
        }

        with self.login_user_context(superuser):
            # Paste plugin from the clipboard into target placeholder
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

        plugins = ph_target.get_plugins('en')
        self.assertTrue(plugins.filter(plugin_type='LinkPlugin').exists())
        self.assertEqual(len(plugins), 2)

        # Paste LinkPlugin as child of first LinkPlugin
        target = ph_target.get_plugins('en').get(position=1)
        data = {
            'plugin_id': plugin.pk,
            'move_a_copy': True,
            'target_language': 'en',
            'target_position': 2,
            'plugin_parent': target.pk,
            'placeholder_id': ph_target.pk,
        }

        with self.login_user_context(superuser):
            # Paste plugin from the clipboard into target placeholder
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

        plugins = ph_target.get_plugins('en')
        self.assertTrue(plugins.filter(plugin_type='LinkPlugin').exists())
        self.assertEqual(len(plugins), 3)

    def test_placeholder_render_ghost_plugin(self):
        """
        Tests a placeholder won't render a ghost plugin.
        """
        page_en = create_page('page_en', 'col_two.html', 'en')
        placeholder_en = page_en.get_placeholders("en").get(slot='col_left')

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
        placeholder_en = page_en.get_placeholders("en").get(slot='col_left')

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
        ###
        # add the test plugin
        ###
        test_plugin = add_plugin(ph1, "EmptyPlugin", "en")
        test_plugin.save()
        endpoint = self.get_change_plugin_uri(test_plugin)
        response = self.client.post(endpoint, {})
        self.assertContains(response, "CMS.API.Helpers.onPluginSave")

    @override_settings(CMS_PERMISSION=False)
    def test_nested_plugin_escapejs_page(self):
        """
        Sibling test of the above, on a page.
        #1366 does not apply to placeholder defined in a page
        """
        page = create_page('page', 'col_two.html', 'en')
        ph1 = page.get_placeholders("en").get(slot='col_left')
        ###
        # add the test plugin
        ###
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
        placeholder_1 = page_en.get_placeholders("en").get(slot='col_left')
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

    def test_plugins_prepopulate(self):
        """ Tests prepopulate placeholder configuration """

        conf = {
            'col_left': {
                'default_plugins': [
                    {
                        'plugin_type': 'TextPlugin',
                        'values': {'body': '<p>en default body 1</p>'},
                    },
                    {
                        'plugin_type': 'TextPlugin',
                        'values': {'body': '<p>en default body 2</p>'},
                    },
                ]
            },
        }
        with self.settings(CMS_PLACEHOLDER_CONF=conf):
            page = create_page('page_en', 'col_two.html', 'en')
            placeholder = page.get_placeholders("en").get(slot='col_left')
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
            placeholder = page.get_placeholders("en").get(slot='col_left')
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
        page = create_page("page", "nav_playground.html", "en")
        title = page.get_content_obj("en")
        for placeholder in page.get_placeholders("en"):
            title.placeholders.remove(placeholder)
            placeholder.pk += 1000
            placeholder.save()
            title.placeholders.add(placeholder)
        page.reload()
        for placeholder in page.get_placeholders("en"):
            add_plugin(placeholder, "TextPlugin", "en", body="body")
        with self.settings(USE_THOUSAND_SEPARATOR=True, USE_L10N=True):
            # Superuser
            user = self.get_superuser()
            self.client.login(username=getattr(user, get_user_model().USERNAME_FIELD),
                              password=getattr(user, get_user_model().USERNAME_FIELD))
            endpoint = get_object_edit_url(title)
            response = self.client.get(endpoint)
            for placeholder in page.get_placeholders("en"):
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
        avail_langs = set(['en', 'de', 'fr'])
        # Setup instance
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        ###
        # add the test plugin
        ###
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
        avail_langs = set(['en', 'de', 'fr'])
        # Setup instances
        page = create_page('test page', 'col_two.html', 'en')
        for lang in avail_langs:
            if lang != 'en':
                create_page_content(lang, 'test page %s' % lang, page)
        placeholder = page.get_placeholders("en").get(slot='col_sidebar')
        ###
        # add the test plugin
        ###
        for lang in avail_langs:
            add_plugin(placeholder, "EmptyPlugin", lang)
        # reload placeholder from database
        placeholder = page.get_placeholders("en").get(slot='col_sidebar')
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
        self.assertEqual(['Whee'], [o for o in output.split('\n') if 'Whee' in o])

        _get_placeholder_slots("placeholder_tests/test_super_extends_2.html")

        template = get_template("placeholder_tests/test_super_extends_2.html")
        output = template.render({})
        self.assertEqual(['Whee'], [o for o in output.split('\n') if 'Whee' in o])

    def test_sets_source_when_title_is_created(self):
        """
        This tests when a title is created, the source field for the
        created placeholders are set to that title.
        """
        page = create_page('test page en', 'col_two.html', 'en')

        # check for en
        page_content_en = self.get_pagecontent_obj(page)
        self.assertQuerySetEqual(
            Placeholder.objects.get_for_obj(page_content_en),
            page_content_en.get_placeholders(),
            transform=lambda x: x,
            ordered=False,
        )

        # check for another language = de
        page_content_de = create_page_content('de', 'test page de', page)
        self.assertQuerySetEqual(
            Placeholder.objects.get_for_obj(page_content_de),
            page_content_de.get_placeholders(),
            transform=lambda x: x,
            ordered=False,
        )

    def test_sets_source_when_title_is_copied(self):
        """
        This tests when a title is copied, the source field for the
        created placeholders are set to the new title.
        """
        page = create_page('source page', 'col_two.html', 'en')

        with self.login_user_context(self.get_superuser()):
            new_page = self.copy_page(page, page, position=1)

        page_content = self.get_pagecontent_obj(page)
        new_page_content = self.get_pagecontent_obj(new_page)
        page_content_plhs = Placeholder.objects.get_for_obj(page_content)
        new_page_content_plhs = Placeholder.objects.get_for_obj(new_page_content)
        self.assertEqual(page_content_plhs.count(), new_page_content_plhs.count())

    def test_sets_source_when_external_object_is_rendered(self):
        """
        This tests the implementation for external objects to use the {% placeholder %}
        template tag where placeholders are created with the source field
        set to the current object.
        """
        from cms.utils.placeholder import get_declared_placeholders_for_obj

        poll = FancyPoll.objects.create(name='poll 1')

        # Go to the poll for the first time
        response = self.client.get(poll.get_absolute_url())
        placeholders = Placeholder.objects.get_for_obj(poll)
        self.assertEqual(placeholders.count(), 2)

        # Now go to edit mode
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(get_object_edit_url(poll))

        placeholders = Placeholder.objects.get_for_obj(poll)
        self.assertEqual(placeholders.count(), 2)

        # Now go to structure mode
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(get_object_structure_url(poll))

        placeholders = Placeholder.objects.get_for_obj(poll)
        self.assertEqual(placeholders.count(), 2)
        declared_placeholders = get_declared_placeholders_for_obj(poll)
        self.assertEqual(len(declared_placeholders), 2)

        for placeholder in declared_placeholders:
            self.assertContains(
                response,
                '<script data-cms id="cms-plugin-child-classes-%s" type="text/cms-template">'
                % placeholders.get(slot=placeholder.slot).pk
            )

        # Change the template
        poll.template = 'fancy_poll_app/detail2.html'
        poll.save()

        # Now go to structure mode again
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(get_object_structure_url(poll))

        placeholders = Placeholder.objects.get_for_obj(poll)
        # By this time rescanning should have occurred
        # and created new placeholders
        placeholders = Placeholder.objects.get_for_obj(poll)
        self.assertEqual(placeholders.count(), 5)
        declared_placeholders = get_declared_placeholders_for_obj(poll)
        self.assertEqual(len(declared_placeholders), 3)

        for placeholder in declared_placeholders:
            self.assertContains(
                response,
                '<script data-cms id="cms-plugin-child-classes-%s" type="text/cms-template">'
                % placeholders.get(slot=placeholder.slot).pk
            )

    def test_placeholder_relation_field(self):
        """
        This tests the PlaceholderRelationField where it returns (does a reverse relation)
        the placeholders for the attached object.
        """
        poll = FancyPoll.objects.create(name='poll 1')

        with self.login_user_context(self.get_superuser()):
            self.client.get(get_object_edit_url(poll))

        self.assertQuerySetEqual(
            poll.placeholders.all(),
            Placeholder.objects.get_for_obj(poll),
            transform=lambda x: x,
            ordered=False
        )

    def test_placeholder_relation_field_get_slot(self):
        """
        This tests the get slot method of PlaceholderRelationField
        """

        from cms.utils.placeholder import get_placeholder_from_slot

        poll = FancyPoll.objects.create(name='poll 1')
        slot_1 = get_placeholder_from_slot(poll.placeholders, slot="slot_1")  # Get placeholder
        self.assertTrue(isinstance(slot_1, Placeholder))  # Correct type
        self.assertEqual(slot_1.slot, "slot_1")  # Correct slot
        self.assertEqual(poll.placeholders.all().count(), 1)  # Has been created?

        slot_2 = get_placeholder_from_slot(poll.placeholders, "slot_2")  # Get 2nd placeholder
        self.assertEqual(slot_2.slot, "slot_2")  # right slot
        self.assertEqual(poll.placeholders.all().count(), 2)  # Two should have been created

        self.assertEqual(slot_1, get_placeholder_from_slot(poll.placeholders, "slot_1"))  # Still the first slot


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
        self.assertEqual(set(fr_copy_languages), set([EN]))
        self.assertEqual(set(de_copy_languages), set([EN, FR]))
        self.assertEqual(set(en_copy_languages), set([FR]))

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
        self.assertEqual(result, None)  # Simple PH - no model

    def test_excercise_get_attached_field(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        self.assertEqual(ph._get_attached_field(), None)  # Simple PH - no field name

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
        self.assertEqual(result, [Example1])  # Simple PH - Example1 model
        add_plugin(ph, 'TextPlugin', 'en', body='en body')
        result = list(ph._get_attached_models())
        self.assertEqual(result, [Example1])  # Simple PH still one Example1 model

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
        self.assertEqual(result, ['placeholder'])  # Simple PH - placeholder field name
        add_plugin(ph, 'TextPlugin', 'en', body='en body')
        result = [f.name for f in list(ph._get_attached_fields())]
        self.assertEqual(result, ['placeholder'])  # Simple PH - still one placeholder field name

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
        placeholder = page.get_placeholders('en').get(slot='col_left')
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
        placeholder = page.get_placeholders("en").get(slot='col_left')
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


class PlaceholderPluginTestsBase(CMSTestCase):

    def _create_placeholder(self, slot='main'):
        return Placeholder.objects.create(slot=slot)

    def _create_plugin(self, placeholder, position, parent=None):
        base = CMSPlugin.objects.create(
            language='en',
            plugin_type='StylePlugin',
            parent=parent,
            position=position,
            placeholder=placeholder,
        )
        plugin_model = base.get_plugin_class().model
        plugin = plugin_model()
        base.set_base_attr(plugin)
        plugin.save()
        return plugin

    def _unpack_descendants(self, parent):
        for child in parent.cmsplugin_set.all():
            yield child.pk

            for desc in self._unpack_descendants(child):
                yield desc

    def setUp(self):
        self.placeholder = self._create_placeholder()
        self.create_plugins(self.placeholder)

    def create_plugins(self, placeholder):
        for i in range(1, 9):
            parent = add_plugin(placeholder or self.placeholder, 'StylePlugin', 'en')
            # self._create_plugin(placeholder, position=i)
            for j in range(3):
                add_plugin(placeholder or self.placeholder, 'StylePlugin', 'en', 'last-child', parent)

    def get_first_root_plugin(self, placeholder=None):
        return self.get_plugins(placeholder).filter(parent__isnull=True).first()

    def get_last_root_plugin(self, placeholder=None):
        return self.get_plugins(placeholder).filter(parent__isnull=True).last()

    def get_plugins(self, placeholder=None):
        if placeholder is None:
            placeholder = self.placeholder
        return CMSPlugin.objects.filter(placeholder=placeholder)

    def get_plugin_tree(self, placeholder=None):
        tree = {}

        for root_plugin in self.get_plugins(placeholder).filter(parent__isnull=True):
            tree[root_plugin.pk] = self.get_plugin_descendants(root_plugin)
        return tree

    def get_plugin_descendants(self, plugin):
        return list(self._unpack_descendants(plugin))

    def assertPluginTreeEquals(self, plugins, placeholder=None):
        """
        plugins should be ordered by position
        """
        new_tree = self.get_plugins(placeholder).values_list('pk', 'position')
        expected = [(pk, pos) for pos, pk in enumerate(plugins, 1)]
        self.assertSequenceEqual(new_tree, expected)


class PlaceholderFlatPluginTests(PlaceholderPluginTestsBase):

    def test_delete(self):
        """
        Deletes all root plugins from the plugin tree,
        one by one, comparing plugin positions at every iteration.
        """
        tree = self.get_plugin_tree()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )

        new_tree = self.get_plugins().values_list('pk', 'position')
        expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
        self.assertSequenceEqual(new_tree, expected)

        for plugin in self.get_plugins().filter(parent__isnull=True):
            for plugin_id in [plugin.pk] + tree[plugin.pk]:
                plugin_tree_all.remove(plugin_id)

            plugin.refresh_from_db()
            self.placeholder.delete_plugin(plugin)

            new_tree = self.get_plugins().values_list('pk', 'position')
            expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
            self.assertSequenceEqual(new_tree, expected)

    def test_move_left(self):
        """
        Moves the last plugin in the tree to the left,
        one step at a time until it reaches the beginning of the tree.
        """
        plugin = self.get_last_root_plugin()
        plugin_tree = [plugin.pk] + self.get_plugin_descendants(plugin)
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )
        positions = list(
            self
            .get_plugins()
            .filter(parent__isnull=True)
            .reverse()
            .exclude(pk=plugin.pk)
            .values_list('pk', 'position')
        )

        for pk, position in positions:
            self.placeholder.move_plugin(plugin, position)
            plugin.refresh_from_db()

            for edge, plugin_id in enumerate(plugin_tree):
                target_index = plugin_tree_all.index(pk)
                plugin_tree_all.remove(plugin_id)
                plugin_tree_all.insert(target_index, plugin_id)
            self.assertPluginTreeEquals(plugin_tree_all)

    def test_move_left_middle(self):
        tree = {}
        root_tree = self.get_plugins().filter(parent__isnull=True)
        count = root_tree.count()
        first_plugin = root_tree.first()
        middle_plugin = root_tree[count // 2]
        last_plugin = root_tree.last()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )

        for root_plugin in [first_plugin, middle_plugin, last_plugin]:
            tree[root_plugin.pk] = list(self._unpack_descendants(root_plugin))

        for target_plugin in [middle_plugin, first_plugin]:
            self.placeholder.move_plugin(last_plugin, target_plugin.position)
            last_plugin.refresh_from_db()

            # Assumes(!) that the children follow directly the parents!
            for edge, plugin_id in enumerate([last_plugin.pk] + tree[last_plugin.pk]):
                target_index = plugin_tree_all.index(target_plugin.pk)
                plugin_tree_all.remove(plugin_id)
                plugin_tree_all.insert(target_index, plugin_id)
            new_tree = self.get_plugins().values_list('pk', 'position')
            expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
            self.assertSequenceEqual(new_tree, expected)

    def test_move_right(self):
        tree = self.get_plugin_tree()
        plugin = self.get_plugins().first()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )
        positions = list(
            self
            .get_plugins()
            .filter(parent__isnull=True)
            .exclude(pk=plugin.pk)
            .values_list('pk', 'position')
        )

        for pk, position in positions:
            self.placeholder.move_plugin(plugin, position)
            plugin.refresh_from_db()
            target_index = plugin_tree_all.index(pk) + len(tree[pk])

            for edge, plugin_id in enumerate([plugin.pk] + tree[plugin.pk]):
                plugin_tree_all.remove(plugin_id)
                plugin_tree_all.insert(target_index, plugin_id)
            new_tree = self.get_plugins().values_list('pk', 'position')
            expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
            self.assertSequenceEqual(new_tree, expected)

    def test_move_right_middle(self):
        tree = {}
        root_tree = self.get_plugins().filter(parent__isnull=True)
        count = root_tree.count()
        first_plugin = root_tree.first()
        middle_plugin = root_tree[count // 2]
        last_plugin = root_tree.last()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )

        for root_plugin in [first_plugin, middle_plugin, last_plugin]:
            tree[root_plugin.pk] = list(self._unpack_descendants(root_plugin))

        for target_plugin in [middle_plugin, last_plugin]:
            self.placeholder.move_plugin(first_plugin, target_plugin.position)
            first_plugin.refresh_from_db()
            target_index = plugin_tree_all.index(target_plugin.pk) + len(tree[target_plugin.pk])

            for edge, plugin_id in enumerate([first_plugin.pk] + tree[first_plugin.pk]):
                plugin_tree_all.remove(plugin_id)
                plugin_tree_all.insert(target_index, plugin_id)
            new_tree = self.get_plugins().values_list('pk', 'position')
            expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
            self.assertSequenceEqual(new_tree, expected)

    def test_move_to_top(self):
        """
        Moves the last plugin in the tree to the top of the tree.
        """
        tree = {}
        first_plugin = self.get_plugins().filter(parent__isnull=True).first()
        last_plugin = self.get_plugins().filter(parent__isnull=True).last()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )

        for root_plugin in [first_plugin, last_plugin]:
            tree[root_plugin.pk] = list(self._unpack_descendants(root_plugin))

        self.placeholder.move_plugin(last_plugin, first_plugin.position)
        last_plugin.refresh_from_db()

        for edge, plugin_id in enumerate([last_plugin.pk] + tree[last_plugin.pk]):
            target_index = plugin_tree_all.index(first_plugin.pk)
            plugin_tree_all.remove(plugin_id)
            plugin_tree_all.insert(target_index, plugin_id)
        new_tree = self.get_plugins().values_list('pk', 'position')
        expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
        self.assertSequenceEqual(new_tree, expected)

    def test_move_to_placeholder_top(self):
        source_plugins = self.get_plugins().filter(parent__isnull=True)
        source_tree_by_root = self.get_plugin_tree()
        source_plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )
        target = self._create_placeholder('target')
        self.create_plugins(target)
        target_plugin_tree_all = list(
            self
            .get_plugins(target)
            .values_list('pk', flat=True)
        )

        for plugin in source_plugins:
            plugin_tree = [plugin.pk] + source_tree_by_root[plugin.pk]
            plugin.refresh_from_db(fields=['position'])
            self.placeholder.move_plugin(plugin, 1, target_placeholder=target)

            for edge, plugin_id in enumerate(plugin_tree):
                source_plugin_tree_all.remove(plugin_id)
                target_plugin_tree_all.insert(edge, plugin_id)
            self.assertPluginTreeEquals(source_plugin_tree_all)
            self.assertPluginTreeEquals(target_plugin_tree_all, placeholder=target)

    def test_move_to_bottom(self):
        tree = {}
        first_plugin = self.get_plugins().first()
        last_plugin = self.get_plugins().last()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )

        for root_plugin in [first_plugin, last_plugin]:
            tree[root_plugin.pk] = list(self._unpack_descendants(root_plugin))

        self.placeholder.move_plugin(first_plugin, last_plugin.position)
        first_plugin.refresh_from_db()
        target_index = plugin_tree_all.index(last_plugin.pk) + len(tree[last_plugin.pk])

        for edge, plugin_id in enumerate([first_plugin.pk] + tree[first_plugin.pk]):
            plugin_tree_all.remove(plugin_id)
            plugin_tree_all.insert(target_index, plugin_id)
        new_tree = self.get_plugins().values_list('pk', 'position')
        expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
        self.assertSequenceEqual(new_tree, expected)

    def test_move_to_placeholder_bottom(self):
        source_plugins = self.get_plugins().filter(parent__isnull=True)
        source_tree_by_root = self.get_plugin_tree()
        source_plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )
        target = self._create_placeholder('target')
        self.create_plugins(target)
        target_plugin_tree_all = list(
            self
            .get_plugins(target)
            .values_list('pk', flat=True)
        )
        target_position = len(target_plugin_tree_all) + 1

        for plugin in source_plugins:
            plugin_tree = [plugin.pk] + source_tree_by_root[plugin.pk]
            plugin.refresh_from_db(fields=['position'])
            self.placeholder.move_plugin(plugin, target_position, target_placeholder=target)

            for edge, plugin_id in enumerate(plugin_tree):
                # target position is 1 indexed
                index = (target_position - 1) + edge
                source_plugin_tree_all.remove(plugin_id)
                target_plugin_tree_all.insert(index, plugin_id)
            target_position += len(plugin_tree)
            self.assertPluginTreeEquals(source_plugin_tree_all)
            self.assertPluginTreeEquals(target_plugin_tree_all, placeholder=target)


class PlaceholderNestedPluginTests(PlaceholderFlatPluginTests):
    """
    Same tests as for PlaceholderFlatPluginTests but now with a different plugin tree:

    ::

        Parent 1
          Parent 2
            Child
        Parent 1
          Parent 2
            Child
        Parent 1
          Parent 2
            Child
        Parent 1
          Parent 2
            Child
    """

    def create_plugins(self, placeholder):
        for i in range(1, 12, 3):
            parent = self._create_plugin(placeholder, position=i)
            parent_2 = self._create_plugin(placeholder, parent=parent, position=i + 1)
            self._create_plugin(placeholder, parent=parent_2, position=i + 2)

    def test_move_to_placeholder_under_parent(self):
        plugin = self.get_plugins().filter(parent__isnull=True).first()
        source_tree_by_root = self.get_plugin_tree()
        source_plugin_tree_all = list(
            self .get_plugins() .values_list('pk', flat=True)
        )
        target = self._create_placeholder('target')
        self.create_plugins(target)
        # Create a single plugin as the first plugin of the target placeholder
        target_plugin = CMSPlugin(language='en', plugin_type='StylePlugin', position=1, placeholder=target)
        target_plugin = target.add_plugin(target_plugin)
        target_plugin_tree_all = list(
            self
            .get_plugins(target)
            .values_list('pk', flat=True)
        )
        plugin_tree = [plugin.pk] + source_tree_by_root[plugin.pk]
        plugin.refresh_from_db(fields=['position'])
        self.placeholder.move_plugin(plugin, 2, target_placeholder=target, target_plugin=target_plugin)

        for edge, plugin_id in enumerate(plugin_tree):
            source_plugin_tree_all.remove(plugin_id)
            target_plugin_tree_all.insert(1 + edge, plugin_id)
        self.assertPluginTreeEquals(source_plugin_tree_all)
        self.assertPluginTreeEquals(target_plugin_tree_all, placeholder=target)

    def test_delete_single(self):
        tree = self.get_plugin_tree()
        plugin_tree_all = list(
            self
            .get_plugins()
            .values_list('pk', flat=True)
        )

        for plugin in self.get_plugins().filter(parent__isnull=True):
            for plugin_id in [plugin.pk] + tree[plugin.pk]:
                plugin_tree_all.remove(plugin_id)

            plugin.refresh_from_db()
            self.placeholder.delete_plugin(plugin)

            new_tree = self.get_plugins().values_list('pk', 'position')
            expected = [(pk, pos) for pos, pk in enumerate(plugin_tree_all, 1)]
            self.assertSequenceEqual(new_tree, expected)
