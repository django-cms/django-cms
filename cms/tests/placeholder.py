# -*- coding: utf-8 -*-
from __future__ import with_statement
import itertools
import warnings

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.messages.storage import default_storage
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpResponseForbidden, HttpResponse
from django.template import TemplateSyntaxError, Template
from django.template.context import Context, RequestContext
from django.template.loader import get_template
from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from django.utils.numberformat import format
from djangocms_link.cms_plugins import LinkPlugin
from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text
from sekizai.context import SekizaiContext

from cms import constants
from cms.admin.placeholderadmin import PlaceholderAdmin, PlaceholderAdminMixin
from cms.api import add_plugin, create_page, create_title
from cms.exceptions import DuplicatePlaceholderWarning
from cms.models.fields import PlaceholderField
from cms.models.placeholdermodel import Placeholder
from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import render_placeholder
from cms.test_utils.fixtures.fakemlng import FakemlngFixtures
from cms.test_utils.project.fakemlng.models import Translations
from cms.test_utils.project.objectpermissionsapp.models import UserObjectPermission
from cms.test_utils.project.placeholderapp.models import (
    DynamicPlaceholderSlotExample,
    Example1,
    MultilingualExample1,
    TwoPlaceholderExample,
)
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import (SettingsOverride, UserLoginContext)
from cms.test_utils.util.mock import AttributeObject
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.compat.dj import force_unicode, get_user_model
from cms.utils.compat.tests import UnittestCompatMixin
from cms.utils.conf import get_cms_setting
from cms.utils.placeholder import PlaceholderNoAction, MLNGPlaceholderActions, get_placeholder_conf
from cms.utils.plugins import get_placeholders, assign_plugins
from cms.utils.urlutils import admin_reverse


class PlaceholderTestCase(CMSTestCase, UnittestCompatMixin):
    def setUp(self):
        u = self._create_user("test", True, True)

        self._login_context = self.login_user_context(u)
        self._login_context.__enter__()

    def tearDown(self):
        self._login_context.__exit__(None, None, None)

    def test_placeholder_scanning_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_one.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'three']))

    def test_placeholder_scanning_sekizai_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_one_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'three']))

    def test_placeholder_scanning_include(self):
        placeholders = get_placeholders('placeholder_tests/test_two.html')
        self.assertEqual(sorted(placeholders), sorted([u'child', u'three']))

    def test_placeholder_scanning_double_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_three.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'new_three']))

    def test_placeholder_scanning_sekizai_double_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_three_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'new_three']))

    def test_placeholder_scanning_complex(self):
        placeholders = get_placeholders('placeholder_tests/test_four.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'child', u'four']))

    def test_placeholder_scanning_super(self):
        placeholders = get_placeholders('placeholder_tests/test_five.html')
        self.assertEqual(sorted(placeholders), sorted([u'one', u'extra_one', u'two', u'three']))

    def test_placeholder_scanning_nested(self):
        placeholders = get_placeholders('placeholder_tests/test_six.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'new_two', u'new_three']))

    def test_placeholder_scanning_duplicate(self):
        placeholders = self.assertWarns(DuplicatePlaceholderWarning,
                                        'Duplicate {% placeholder "one" %} in template placeholder_tests/test_seven.html.',
                                        get_placeholders, 'placeholder_tests/test_seven.html')
        self.assertEqual(sorted(placeholders), sorted([u'one']))

    def test_placeholder_scanning_extend_outside_block(self):
        placeholders = get_placeholders('placeholder_tests/outside.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

    def test_placeholder_scanning_sekizai_extend_outside_block(self):
        placeholders = get_placeholders('placeholder_tests/outside_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

    def test_placeholder_scanning_extend_outside_block_nested(self):
        placeholders = get_placeholders('placeholder_tests/outside_nested.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

    def test_placeholder_scanning_sekizai_extend_outside_block_nested(self):
        placeholders = get_placeholders('placeholder_tests/outside_nested_sekizai.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

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
        ph1_pl1 = add_plugin(ph1, TextPlugin, 'en', body='ph1 plugin1').cmsplugin_ptr
        ph1_pl2 = add_plugin(ph1, TextPlugin, 'en', body='ph1 plugin2').cmsplugin_ptr
        ph1_pl3 = add_plugin(ph1, TextPlugin, 'en', body='ph1 plugin3').cmsplugin_ptr
        ph2_pl1 = add_plugin(ph2, TextPlugin, 'en', body='ph2 plugin1').cmsplugin_ptr
        ph2_pl2 = add_plugin(ph2, TextPlugin, 'en', body='ph2 plugin2').cmsplugin_ptr
        ph2_pl3 = add_plugin(ph2, TextPlugin, 'en', body='ph2 plugin3').cmsplugin_ptr
        response = self.client.post(admin_reverse('placeholderapp_twoplaceholderexample_move_plugin'), {
            'placeholder_id': str(ph2.pk),
            'plugin_id': str(ph1_pl2.pk),
            'plugin_order[]': [str(p.pk) for p in [ph2_pl3, ph2_pl1, ph2_pl2, ph1_pl2]]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual([ph1_pl1, ph1_pl3], list(ph1.cmsplugin_set.order_by('position')))
        self.assertEqual([ph2_pl3, ph2_pl1, ph2_pl2, ph1_pl2, ], list(ph2.cmsplugin_set.order_by('position')))

    def test_nested_plugin_escapejs(self):
        """
        Checks #1366 error condition.
        When adding/editing a plugin whose icon_src() method returns a URL
        containing an hyphen, the hyphen is escaped by django escapejs resulting
        in a incorrect URL
        """
        with SettingsOverride(CMS_PERMISSION=False):
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
            test_plugin = add_plugin(ph1, u"EmptyPlugin", u"en")
            test_plugin.save()
            pl_url = "%sedit-plugin/%s/" % (
                admin_reverse('placeholderapp_example1_change', args=(ex.pk,)),
                test_plugin.pk)
            response = self.client.post(pl_url, {})
            self.assertContains(response, "CMS.API.Helpers.reloadBrowser")

    def test_nested_plugin_escapejs_page(self):
        """
        Sibling test of the above, on a page.
        #1366 does not apply to placeholder defined in a page
        """
        with SettingsOverride(CMS_PERMISSION=False):
            page = create_page('page', 'col_two.html', 'en')
            ph1 = page.placeholders.get(slot='col_left')
            ###
            # add the test plugin
            ###
            test_plugin = add_plugin(ph1, u"EmptyPlugin", u"en")
            test_plugin.save()
            pl_url = "%sedit-plugin/%s/" % (
                admin_reverse('cms_page_change', args=(page.pk,)),
                test_plugin.pk)
            response = self.client.post(pl_url, {})
            self.assertContains(response, "CMS.API.Helpers.reloadBrowser")

    def test_placeholder_scanning_fail(self):
        self.assertRaises(TemplateSyntaxError, get_placeholders, 'placeholder_tests/test_eleven.html')

    def test_placeholder_tag(self):
        template = Template("{% load cms_tags %}{% render_placeholder placeholder %}")
        ctx = Context()
        self.assertEqual(template.render(ctx), "")
        request = self.get_request('/')
        rctx = RequestContext(request)
        self.assertEqual(template.render(rctx), "")
        placeholder = Placeholder.objects.create(slot="test")
        rctx['placeholder'] = placeholder
        self.assertEqual(template.render(rctx), "")
        self.assertEqual(placeholder.cmsplugin_set.count(), 0)
        add_plugin(placeholder, "TextPlugin", settings.LANGUAGES[0][0], body="test")
        self.assertEqual(placeholder.cmsplugin_set.count(), 1)
        rctx = RequestContext(request)
        placeholder = self.reload(placeholder)
        rctx['placeholder'] = placeholder
        self.assertEqual(template.render(rctx).strip(), "test")

    def test_placeholder_tag_language(self):
        template = Template("{% load cms_tags %}{% render_placeholder placeholder language language %}")
        placeholder = Placeholder.objects.create(slot="test")
        add_plugin(placeholder, "TextPlugin", 'en', body="English")
        add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")
        request = self.get_request('/')
        rctx = RequestContext(request)
        rctx['placeholder'] = placeholder
        rctx['language'] = 'en'
        self.assertEqual(template.render(rctx).strip(), "English")
        del placeholder._plugins_cache
        rctx['language'] = 'de'
        self.assertEqual(template.render(rctx).strip(), "Deutsch")

    def test_get_placeholder_conf(self):
        TEST_CONF = {
            'main': {
                'name': 'main content',
                'plugins': ['TextPlugin', 'LinkPlugin'],
                'default_plugins':[
                    {
                        'plugin_type':'TextPlugin', 
                        'values':{
                            'body':'<p>Some default text</p>'
                        },
                    },
                ],
            },
            'layout/home.html main': {
                'name': u'main content with FilerImagePlugin and limit',
                'plugins': ['TextPlugin', 'FilerImagePlugin', 'LinkPlugin',],
                'inherit':'main',
                'limits': {'global': 1,},
            },
            'layout/other.html main': {
                'name': u'main content with FilerImagePlugin and no limit',
                'inherit':'layout/home.html main',
                'limits': {},
            },
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=TEST_CONF):
            #test no inheritance
            returned = get_placeholder_conf('plugins', 'main')
            self.assertEqual(returned, TEST_CONF['main']['plugins'])
            #test no inherited value with inheritance enabled
            returned = get_placeholder_conf('plugins', 'main', 'layout/home.html')
            self.assertEqual(returned, TEST_CONF['layout/home.html main']['plugins'])
            #test direct inherited value
            returned = get_placeholder_conf('plugins', 'main', 'layout/other.html')
            self.assertEqual(returned, TEST_CONF['layout/home.html main']['plugins'])
            #test grandparent inherited value
            returned = get_placeholder_conf('default_plugins', 'main', 'layout/other.html')
            self.assertEqual(returned, TEST_CONF['main']['default_plugins'])

    def test_placeholder_context_leaking(self):
        TEST_CONF = {'test': {'extra_context': {'width': 10}}}
        ph = Placeholder.objects.create(slot='test')

        class NoPushPopContext(Context):
            def push(self):
                pass

            pop = push

        context = NoPushPopContext()
        context['request'] = self.get_request()
        with SettingsOverride(CMS_PLACEHOLDER_CONF=TEST_CONF):
            render_placeholder(ph, context)
            self.assertTrue('width' in context)
            self.assertEqual(context['width'], 10)
            ph.render(context, None)
            self.assertTrue('width' in context)
            self.assertEqual(context['width'], 10)

    def test_placeholder_scanning_nested_super(self):
        placeholders = get_placeholders('placeholder_tests/nested_super_level1.html')
        self.assertEqual(sorted(placeholders), sorted([u'level1', u'level2', u'level3', u'level4']))

    def test_placeholder_field_no_related_name(self):
        self.assertRaises(ValueError, PlaceholderField, 'placeholder', related_name='+')

    def test_placeholder_field_db_table(self):
        """
        Test for leaking Django 1.7 Model._meta.db_table monkeypatching
        on sqlite See #3891
        This test for a side-effect of the above which prevents placeholder
        fields to return the 
        """
        example = Category.objects.create(
            name='category',
            parent=None
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
        add_plugin(placeholder_en, TextPlugin, 'en', body='en body')

        class NoPushPopContext(SekizaiContext):
            def push(self):
                pass

            pop = push

        context_en = NoPushPopContext()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_de = NoPushPopContext()
        context_de['request'] = self.get_request(language="de", page=page_en)

        # First test the default (non-fallback) behavior)
        ## English page should have the text plugin
        content_en = render_placeholder(placeholder_en, context_en)
        self.assertRegexpMatches(content_en, "^en body$")

        ## Deutsch page should have no text
        content_de = render_placeholder(placeholder_de, context_de)
        self.assertNotRegex(content_de, "^en body$")
        self.assertEqual(len(content_de), 0)

        conf = {
            'col_left': {
                'language_fallback': True,
            },
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            ## Deutsch page should have no text
            del(placeholder_de._plugins_cache)
            cache.clear()
            content_de = render_placeholder(placeholder_de, context_de)
            self.assertRegexpMatches(content_de, "^en body$")
            context_de2 = NoPushPopContext()
            request = self.get_request(language="de", page=page_en)
            request.user = self.get_superuser()
            request.toolbar = CMSToolbar(request)
            request.toolbar.edit_mode = True
            context_de2['request'] = request
            del(placeholder_de._plugins_cache)
            cache.clear()
            content_de2 = render_placeholder(placeholder_de, context_de2)
            self.assertFalse("en body" in content_de2)
            # remove the cached plugins instances
            del(placeholder_de._plugins_cache)
            cache.clear()
            # Then we add a plugin to check for proper rendering
            add_plugin(placeholder_de, TextPlugin, 'de', body='de body')
            content_de = render_placeholder(placeholder_de, context_de)
            self.assertRegexpMatches(content_de, "^de body$")

    def test_plugins_non_default_language_fallback(self):
        """ Tests language_fallback placeholder configuration """
        page_en = create_page('page_en', 'col_two.html', 'en')
        create_title("de", "page_de", page_en)
        placeholder_en = page_en.placeholders.get(slot='col_left')
        placeholder_de = page_en.placeholders.get(slot='col_left')
        add_plugin(placeholder_de, TextPlugin, 'de', body='de body')

        class NoPushPopContext(Context):
            def push(self):
                pass

            pop = push

        context_en = NoPushPopContext()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_de = NoPushPopContext()
        context_de['request'] = self.get_request(language="de", page=page_en)

        # First test the default (non-fallback) behavior)
        ## Deutsch page should have the text plugin
        content_de = render_placeholder(placeholder_en, context_de)
        self.assertRegexpMatches(content_de, "^de body$")
        del(placeholder_en._plugins_cache)
        cache.clear()
        ## English page should have no text
        content_en = render_placeholder(placeholder_en, context_en)
        self.assertNotRegex(content_en, "^de body$")
        self.assertEqual(len(content_en), 0)
        del(placeholder_en._plugins_cache)
        cache.clear()
        conf = {
            'col_left': {
                'language_fallback': True,
            },
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            ## English page should have deutsch text
            content_en = render_placeholder(placeholder_en, context_en)
            self.assertRegexpMatches(content_en, "^de body$")

            # remove the cached plugins instances
            del(placeholder_en._plugins_cache)
            cache.clear()
            # Then we add a plugin to check for proper rendering
            add_plugin(placeholder_en, TextPlugin, 'en', body='en body')
            content_en = render_placeholder(placeholder_en, context_en)
            self.assertRegexpMatches(content_en, "^en body$")

    def test_plugins_discarded_with_language_fallback(self):
        """
        Tests side effect of language fallback: if fallback enabled placeholder
        existed, it discards all other existing plugins
        """
        page_en = create_page('page_en', 'col_two.html', 'en')
        create_title("de", "page_de", page_en)
        placeholder_sidebar_en = page_en.placeholders.get(slot='col_sidebar')
        placeholder_en = page_en.placeholders.get(slot='col_left')
        add_plugin(placeholder_sidebar_en, TextPlugin, 'en', body='en body')

        class NoPushPopContext(Context):
            def push(self):
                pass

            pop = push

        context_en = NoPushPopContext()
        context_en['request'] = self.get_request(language="en", page=page_en)

        conf = {
            'col_left': {
                'language_fallback': True,
            },
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            # call assign plugins first, as this is what is done in real cms life
            # for all placeholders in a page at once
            assign_plugins(context_en['request'],
                           [placeholder_sidebar_en, placeholder_en], 'col_two.html')
            # if the normal, non fallback enabled placeholder still has content
            content_en = render_placeholder(placeholder_sidebar_en, context_en)
            self.assertRegexpMatches(content_en, "^en body$")

            # remove the cached plugins instances
            del(placeholder_sidebar_en._plugins_cache)
            cache.clear()

    def test_plugins_prepopulate(self):
        """ Tests prepopulate placeholder configuration """

        class NoPushPopContext(Context):
            def push(self):
                pass

            pop = push

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
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            page = create_page('page_en', 'col_two.html', 'en')
            placeholder = page.placeholders.get(slot='col_left')
            context = NoPushPopContext()
            context['request'] = self.get_request(language="en", page=page)
            # Our page should have "en default body 1" AND "en default body 2"
            content = render_placeholder(placeholder, context)
            self.assertRegexpMatches(content, "^<p>en default body 1</p>\s*<p>en default body 2</p>$")


    def test_plugins_children_prepopulate(self):
        """
        Validate a default textplugin with a nested default link plugin
        """
        
        class NoPushPopContext(Context):
            def push(self):
                pass

            pop = push

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
                                    'url': 'https://www.djangoproject.com/'
                                },
                            },
                            {
                                'plugin_type': 'LinkPlugin',
                                'values': {
                                    'name': 'django-cms',
                                    'url': 'https://www.django-cms.org'
                                },
                            },
                        ]
                    },
                ]
            },
        }

        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            page = create_page('page_en', 'col_two.html', 'en')
            placeholder = page.placeholders.get(slot='col_left')
            context = NoPushPopContext()
            context['request'] = self.get_request(language="en", page=page)
            render_placeholder(placeholder, context)
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
            add_plugin(placeholder, "TextPlugin", "en", body="body",
                       id=placeholder.pk)
        with SettingsOverride(USE_THOUSAND_SEPARATOR=True, USE_L10N=True):
            # Superuser
            user = self.get_superuser()
            self.client.login(username=getattr(user, get_user_model().USERNAME_FIELD),
                              password=getattr(user, get_user_model().USERNAME_FIELD))
            response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            for placeholder in page.placeholders.all():
                self.assertContains(
                    response, "'placeholder_id': '%s'" % placeholder.pk)
                self.assertNotContains(
                    response, "'placeholder_id': '%s'" % format(
                        placeholder.pk, ".", grouping=3, thousand_sep=","))
                self.assertNotContains(
                    response, "'plugin_id': '%s'" % format(
                        placeholder.pk, ".", grouping=3, thousand_sep=","))
                self.assertNotContains(
                    response, "'clipboard': '%s'" % format(
                        response.context['request'].toolbar.clipboard.pk, ".",
                        grouping=3, thousand_sep=","))

    def test_placeholder_languages_model(self):
        """
        Checks the retrieval of filled languages for a placeholder in a django
        model
        """
        avail_langs = set([u'en', u'de', u'fr'])
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
            add_plugin(ex.placeholder, u"EmptyPlugin", lang)
        # reload instance from database
        ex = Example1.objects.get(pk=ex.pk)
        #get languages
        langs = [lang['code'] for lang in ex.placeholder.get_filled_languages()]
        self.assertEqual(avail_langs, set(langs))

    def test_placeholder_languages_page(self):
        """
        Checks the retrieval of filled languages for a placeholder in a django
        model
        """
        avail_langs = set([u'en', u'de', u'fr'])
        # Setup instances
        page = create_page('test page', 'col_two.html', u'en')
        for lang in avail_langs:
            if lang != u'en':
                create_title(lang, 'test page %s' % lang, page)
        placeholder = page.placeholders.get(slot='col_sidebar')
        ###
        # add the test plugin
        ###
        for lang in avail_langs:
            add_plugin(placeholder, u"EmptyPlugin", lang)
        # reload placeholder from database
        placeholder = page.placeholders.get(slot='col_sidebar')
        # get languages
        langs = [lang['code'] for lang in placeholder.get_filled_languages()]
        self.assertEqual(avail_langs, set(langs))

    def test_deprecated_PlaceholderAdmin(self):
        admin_site = admin.sites.AdminSite()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            pa = PlaceholderAdmin(Placeholder, admin_site)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertTrue("PlaceholderAdminMixin with admin.ModelAdmin" in str(w[-1].message))
            self.assertIsInstance(pa, admin.ModelAdmin, 'PlaceholderAdmin not admin.ModelAdmin')
            self.assertIsInstance(pa, PlaceholderAdminMixin, 'PlaceholderAdmin not PlaceholderAdminMixin')

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
    
        self.assertNotIn('one',
            get_template("placeholder_tests/test_super_extends_2.html").nodelist[0].blocks.keys(),
            "test_super_extends_1.html contains a block called 'one', "
            "but _2.html does not.")

        get_placeholders("placeholder_tests/test_super_extends_2.html")

        self.assertNotIn('one',
            get_template("placeholder_tests/test_super_extends_2.html").nodelist[0].blocks.keys(),
            "test_super_extends_1.html still should not contain a block "
            "called 'one' after rescanning placeholders.")

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
        output = template.render(Context({}))
        self.assertEqual(['Whee'], [o for o in output.split('\n')
            if 'Whee' in o])
          
        get_placeholders("placeholder_tests/test_super_extends_2.html")

        template = get_template("placeholder_tests/test_super_extends_2.html")
        output = template.render(Context({}))
        self.assertEqual(['Whee'], [o for o in output.split('\n')
            if 'Whee' in o])


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
        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)

        new_plugins = actions.copy(de.placeholder, 'fr', 'placeholder', Translations, 'de')
        self.assertEqual(len(new_plugins), 1)

        de = self.reload(de)
        fr = self.reload(fr)

        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 1)

    def test_mlng_placeholder_actions_empty_copy(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)

        new_plugins = actions.copy(fr.placeholder, 'de', 'placeholder', Translations, 'fr')
        self.assertEqual(len(new_plugins), 0)

        de = self.reload(de)
        fr = self.reload(fr)

        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)

    def test_mlng_placeholder_actions_no_placeholder(self):
        actions = MLNGPlaceholderActions()
        Translations.objects.filter(language_code='nl').update(placeholder=None)
        de = Translations.objects.get(language_code='de')
        nl = Translations.objects.get(language_code='nl')
        self.assertEqual(nl.placeholder, None)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)

        okay = actions.copy(de.placeholder, 'nl', 'placeholder', Translations, 'de')
        self.assertEqual(okay, False)

        de = self.reload(de)
        nl = self.reload(nl)

        nl = Translations.objects.get(language_code='nl')
        de = Translations.objects.get(language_code='de')


class PlaceholderModelTests(CMSTestCase):
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
        result = ph.has_change_permission(self.get_mock_request(True))
        self.assertTrue(result)

    def test_check_placeholder_permissions_nok_for_user(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph.has_change_permission(self.get_mock_request(False))
        self.assertFalse(result)

    def test_check_unicode_rendering(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = force_unicode(ph)
        self.assertEqual(result, u'test')

    def test_request_placeholders_permission_check_model(self):
        # Setup instance
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        page_en = create_page('page_en', 'col_two.html', 'en')

        class NoPushPopContext(SekizaiContext):
            def push(self):
                pass

            pop = push

        context_en = NoPushPopContext()

        # no user: no placeholders but no error either
        factory = RequestFactory()
        context_en['request'] = factory.get(page_en.get_absolute_url())
        render_placeholder(ex.placeholder, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 0)
        self.assertNotIn(ex.placeholder, context_en['request'].placeholders)

        # request.placeholders is populated for superuser
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_en['request'].user = self.get_superuser()
        render_placeholder(ex.placeholder, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 1)
        self.assertIn(ex.placeholder, context_en['request'].placeholders)

        # request.placeholders is not populated for staff user with no permission
        user = self.get_staff_user_with_no_permissions()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_en['request'].user = user
        render_placeholder(ex.placeholder, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 0)
        self.assertNotIn(ex.placeholder, context_en['request'].placeholders)

        # request.placeholders is populated for staff user with permission on the model
        user.user_permissions.add(Permission.objects.get(codename='change_example1'))
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_en['request'].user = get_user_model().objects.get(pk=user.pk)
        render_placeholder(ex.placeholder, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 1)
        self.assertIn(ex.placeholder, context_en['request'].placeholders)

    def test_request_placeholders_permission_check_page(self):
        page_en = create_page('page_en', 'col_two.html', 'en')
        placeholder_en = page_en.placeholders.get(slot='col_left')

        class NoPushPopContext(SekizaiContext):
            def push(self):
                pass

            pop = push

        context_en = NoPushPopContext()

        # request.placeholders is populated for superuser
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_en['request'].user = self.get_superuser()
        render_placeholder(placeholder_en, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 1)
        self.assertIn(placeholder_en, context_en['request'].placeholders)

        # request.placeholders is not populated for staff user with no permission
        user = self.get_staff_user_with_no_permissions()
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_en['request'].user = user
        render_placeholder(placeholder_en, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 0)
        self.assertNotIn(placeholder_en, context_en['request'].placeholders)

        # request.placeholders is populated for staff user with permission on the model
        user.user_permissions.add(Permission.objects.get(codename='change_page'))
        context_en['request'] = self.get_request(language="en", page=page_en)
        context_en['request'].user = get_user_model().objects.get(pk=user.pk)
        render_placeholder(placeholder_en, context_en)
        self.assertEqual(len(context_en['request'].placeholders), 1)
        self.assertIn(placeholder_en, context_en['request'].placeholders)

    def test_request_placeholders_permission_check_templatetag(self):
        """
        Tests that {% render_placeholder %} templatetag check for placeholder permission
        """
        page_en = create_page('page_en', 'col_two.html', 'en')
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template = '{% load cms_tags %}{% render_placeholder ex1.placeholder %}'

        context = RequestContext(self.get_request(language="en", page=page_en), {'ex1': ex1})

        # request.placeholders is populated for superuser
        context['request'] = self.get_request(language="en", page=page_en)
        context['request'].user = self.get_superuser()
        template_obj = Template(template)
        template_obj.render(context)
        self.assertEqual(len(context['request'].placeholders), 2)
        self.assertIn(ex1.placeholder, context['request'].placeholders)

        # request.placeholders is not populated for staff user with no permission
        user = self.get_staff_user_with_no_permissions()
        context['request'] = self.get_request(language="en", page=page_en)
        context['request'].user = user
        template_obj = Template(template)
        template_obj.render(context)
        self.assertEqual(len(context['request'].placeholders), 0)
        self.assertNotIn(ex1.placeholder, context['request'].placeholders)

        # request.placeholders is populated for staff user with permission on the model
        user.user_permissions.add(Permission.objects.get(codename='change_example1'))
        context['request'] = self.get_request(language="en", page=page_en)
        context['request'].user = get_user_model().objects.get(pk=user.pk)
        template_obj = Template(template)
        template_obj.render(context)
        self.assertEqual(len(context['request'].placeholders), 2)
        self.assertIn(ex1.placeholder, context['request'].placeholders)

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
        add_plugin(ph, TextPlugin, 'en', body='en body')
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
        add_plugin(ph, TextPlugin, 'en', body='en body')
        result = [f.name for f in list(ph._get_attached_fields())]
        self.assertEqual(result, ['placeholder']) # Simple PH - still one placeholder field name


class PlaceholderAdminTestBase(CMSTestCase):
    def get_placeholder(self):
        return Placeholder.objects.create(slot='test')

    def get_admin(self):
        admin.autodiscover()
        return admin.site._registry[Example1]

    def get_post_request(self, data):
        return self.get_request(post_data=data)


class PlaceholderAdminTest(PlaceholderAdminTestBase):
    placeholderconf = {'test': {
        'limits': {
            'global': 2,
            'TextPlugin': 1,
        }
    }
    }

    def test_global_limit(self):
        placeholder = self.get_placeholder()
        admin_instance = self.get_admin()
        data = {
            'plugin_type': 'LinkPlugin',
            'placeholder_id': placeholder.pk,
            'plugin_language': 'en',
        }
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(data)
                response = admin_instance.add_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                response = admin_instance.add_plugin(request) # second
                self.assertEqual(response.status_code, 200)
                response = admin_instance.add_plugin(request) # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, b"This placeholder already has the maximum number of plugins (2).")

    def test_type_limit(self):
        placeholder = self.get_placeholder()
        admin_instance = self.get_admin()
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder_id': placeholder.pk,
            'plugin_language': 'en',
        }
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(data)
                response = admin_instance.add_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                response = admin_instance.add_plugin(request) # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content,
                                 b"This placeholder already has the maximum number (1) of allowed Text plugins.")

    def test_global_limit_on_plugin_move(self):
        admin_instance = self.get_admin()
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot='source')
        target_placeholder = self.get_placeholder()
        data = {
            'placeholder': source_placeholder,
            'plugin_type': 'LinkPlugin',
            'language': 'en',
        }
        plugin_1 = add_plugin(**data)
        plugin_2 = add_plugin(**data)
        plugin_3 = add_plugin(**data)
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request({'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_1.pk})
                response = admin_instance.move_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                request = self.get_post_request({'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_2.pk})
                response = admin_instance.move_plugin(request) # second
                self.assertEqual(response.status_code, 200)
                request = self.get_post_request({'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_3.pk})
                response = admin_instance.move_plugin(request) # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, b"This placeholder already has the maximum number of plugins (2).")

    def test_type_limit_on_plugin_move(self):
        admin_instance = self.get_admin()
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot='source')
        target_placeholder = self.get_placeholder()
        data = {
            'placeholder': source_placeholder,
            'plugin_type': 'TextPlugin',
            'language': 'en',
        }
        plugin_1 = add_plugin(**data)
        plugin_2 = add_plugin(**data)
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request({'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_1.pk})
                response = admin_instance.move_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                request = self.get_post_request({'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_2.pk})
                response = admin_instance.move_plugin(request) # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content,
                                 b"This placeholder already has the maximum number (1) of allowed Text plugins.")

    def test_no_limit_check_same_placeholder_move(self):
        admin_instance = self.get_admin()
        superuser = self.get_superuser()
        source_placeholder = self.get_placeholder()
        data = {
            'placeholder': source_placeholder,
            'plugin_type': 'LinkPlugin',
            'language': 'en',
        }
        plugin_1 = add_plugin(**data)
        add_plugin(**data)
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request({'placeholder_id': source_placeholder.pk, 'plugin_id': plugin_1.pk,
                                                 'plugin_order': 1, })
                response = admin_instance.move_plugin(request) # first
                self.assertEqual(response.status_code, 200)

    def test_edit_plugin_and_cancel(self):
        placeholder = self.get_placeholder()
        admin_instance = self.get_admin()
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder_id': placeholder.pk,
            'plugin_language': 'en',
        }
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(data)
                response = admin_instance.add_plugin(request)
                self.assertEqual(response.status_code, 200)
                plugin_id = int(str(response.content).split('edit-plugin/')[1].split("/")[0])
                data = {
                    'body': 'Hello World',
                }
                request = self.get_post_request(data)
                response = admin_instance.edit_plugin(request, plugin_id)
                self.assertEqual(response.status_code, 200)
                text_plugin = Text.objects.get(pk=plugin_id)
                self.assertEqual('Hello World', text_plugin.body)

                # edit again, but this time press cancel
                data = {
                    'body': 'Hello World!!',
                    '_cancel': True,
                }
                request = self.get_post_request(data)
                response = admin_instance.edit_plugin(request, plugin_id)
                self.assertEqual(response.status_code, 200)
                text_plugin = Text.objects.get(pk=plugin_id)
                self.assertEqual('Hello World', text_plugin.body)


class PlaceholderPluginPermissionTests(PlaceholderAdminTestBase):
    def _testuser(self):
        User = get_user_model()
        u = User(is_staff=True, is_active=True, is_superuser=False)
        setattr(u, u.USERNAME_FIELD, "test")
        u.set_password("test")
        u.save()
        return u

    def _create_example(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        self._placeholder = ex.placeholder
        self.example_object = ex

    def _create_plugin(self):
        self._plugin = add_plugin(self._placeholder, 'TextPlugin', 'en')

    def _give_permission(self, user, model, permission_type, save=True):
        codename = '%s_%s' % (permission_type, model._meta.object_name.lower())
        user.user_permissions.add(Permission.objects.get(codename=codename))

    def _delete_permission(self, user, model, permission_type, save=True):
        codename = '%s_%s' % (permission_type, model._meta.object_name.lower())
        user.user_permissions.remove(Permission.objects.get(codename=codename))

    def _give_object_permission(self, user, object, permission_type, save=True):
        codename = '%s_%s' % (permission_type, object.__class__._meta.object_name.lower())
        UserObjectPermission.objects.assign_perm(codename, user=user, obj=object)

    def _delete_object_permission(self, user, object, permission_type, save=True):
        codename = '%s_%s' % (permission_type, object.__class__._meta.object_name.lower())
        UserObjectPermission.objects.remove_perm(codename, user=user, obj=object)

    def _post_request(self, user):
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder_id': self._placeholder.pk,
            'plugin_language': 'en',
        }
        request = self.get_post_request(data)
        request.user = self.reload(user)
        request._messages = default_storage(request)
        return request

    def test_plugin_add_requires_permissions(self):
        """User wants to add a plugin to the example app placeholder but has no permissions"""
        self._test_plugin_action_requires_permissions('add')

    def test_plugin_edit_requires_permissions(self):
        """User wants to edit a plugin to the example app placeholder but has no permissions"""
        self._test_plugin_action_requires_permissions('change')

    def _test_plugin_action_requires_permissions(self, key):
        self._create_example()
        if key == 'change':
            self._create_plugin()
        normal_guy = self._testuser()
        admin_instance = self.get_admin()
        # check all combinations of plugin, app and object permission
        for perms in itertools.product(*[[False, True]]*3):
            self._set_perms(normal_guy, [Text, Example1, self.example_object], perms, key)
            request = self._post_request(normal_guy)
            if key == 'add':
                response = admin_instance.add_plugin(request)
            elif key == 'change':
                response = admin_instance.edit_plugin(request, self._plugin.id)
            should_pass = perms[0] and (perms[1] or perms[2])
            expected_status_code = HttpResponse.status_code if should_pass else HttpResponseForbidden.status_code
            self.assertEqual(response.status_code, expected_status_code)
        # cleanup
        self._set_perms(normal_guy, [Text, Example1, self.example_object], (False,)*3, key)

    def _set_perms(self, user, objects, perms, key):
        for obj, perm in zip(objects, perms):
            action = 'give' if perm else 'delete'
            object_key = '_object' if isinstance(obj, models.Model) else ''
            method_name = '_%s%s_permission' % (action, object_key)
            getattr(self, method_name)(user, obj, key)


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
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
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
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            plugins = plugin_pool.get_all_plugins(placeholder, page)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(plugins[0], LinkPlugin)


class PlaceholderI18NTest(CMSTestCase):
    def _testuser(self):
        User = get_user_model()
        u = User(is_staff=True, is_active=True, is_superuser=True)
        setattr(u, u.USERNAME_FIELD, "test")
        u.set_password("test")
        u.save()
        return u

    def test_hvad_tabs(self):
        ex = MultilingualExample1(
            char_1='one',
            char_2='two',
        )
        ex.save()
        self._testuser()
        self.client.login(username='test', password='test')

        response = self.client.get('/de/admin/placeholderapp/multilingualexample1/%d/' % ex.pk)
        self.assertContains(response, '<input type="hidden" class="language_button selected" name="de" />')

    def test_no_tabs(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='one',
            char_4='two',
        )
        ex.save()
        self._testuser()
        self.client.login(username='test', password='test')

        response = self.client.get('/de/admin/placeholderapp/example1/%d/' % ex.pk)
        self.assertNotContains(response, '<input type="hidden" class="language_button selected" name="de" />')

    def test_placeholder_tabs(self):
        ex = TwoPlaceholderExample(
            char_1='one',
            char_2='two',
            char_3='one',
            char_4='two',
        )
        ex.save()
        self._testuser()
        self.client.login(username='test', password='test')

        response = self.client.get('/de/admin/placeholderapp/twoplaceholderexample/%d/' % ex.pk)
        self.assertNotContains(response,
                               """<input type="button" onclick="trigger_lang_button(this,'./?language=en');" class="language_button selected" id="debutton" name="en" value="English">""")


