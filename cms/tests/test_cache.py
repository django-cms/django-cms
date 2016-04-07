# -*- coding: utf-8 -*-
from django.conf import settings
from sekizai.context import SekizaiContext

from cms.api import add_plugin, create_page
from cms.cache import _get_cache_version, invalidate_cms_page_cache
from cms.models import Page
from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import render_placeholder
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.project.pluginapp.plugins.caching.cms_plugins import NoCachePlugin, SekizaiPlugin
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.toolbar import CMSToolbar
from cms.utils import get_cms_setting


class CacheTestCase(CMSTestCase):
    def tearDown(self):
        from django.core.cache import cache
        super(CacheTestCase, self).tearDown()
        cache.clear()

    def setUp(self):
        from django.core.cache import cache
        super(CacheTestCase, self).setUp()
        cache.clear()

    def test_cache_placeholder(self):
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)

        placeholder = page1.placeholders.filter(slot="body")[0]
        add_plugin(placeholder, "TextPlugin", 'en', body="English")
        add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        with self.assertNumQueries(5):
            self.render_template_obj(template, {}, request)
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        request.toolbar.edit_mode = False
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(1):
            self.render_template_obj(template, {}, request)
        # toolbar
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        request.toolbar.edit_mode = True
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(3):
            self.render_template_obj(template, {}, request)
        page1.publish('en')
        exclude = [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware'
        ]
        middleware = [mw for mw in settings.MIDDLEWARE_CLASSES if mw not in exclude]
        with self.settings(CMS_PAGE_CACHE=False, MIDDLEWARE_CLASSES=middleware):
            with self.assertNumQueries(FuzzyInt(13, 22)):
                self.client.get('/en/')
            with self.assertNumQueries(FuzzyInt(5, 9)):
                self.client.get('/en/')
        with self.settings(CMS_PAGE_CACHE=False, MIDDLEWARE_CLASSES=middleware, CMS_PLACEHOLDER_CACHE=False):
            with self.assertNumQueries(FuzzyInt(7, 11)):
                self.client.get('/en/')

    def test_no_cache_plugin(self):
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)

        placeholder1 = page1.placeholders.filter(slot="body")[0]
        placeholder2 = page1.placeholders.filter(slot="right-column")[0]
        plugin_pool.register_plugin(NoCachePlugin)
        add_plugin(placeholder1, "TextPlugin", 'en', body="English")
        add_plugin(placeholder2, "TextPlugin", 'en', body="Deutsch")

        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(3):
            self.render_template_obj(template, {}, request)

        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(1):
            self.render_template_obj(template, {}, request)
        add_plugin(placeholder1, "NoCachePlugin", 'en')
        page1.publish('en')
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(4):
            output = self.render_template_obj(template, {}, request)
        with self.assertNumQueries(FuzzyInt(14, 19)):
            response = self.client.get('/en/')
            resp1 = response.content.decode('utf8').split("$$$")[1]

        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(4):
            output2 = self.render_template_obj(template, {}, request)
        with self.settings(CMS_PAGE_CACHE=False):
            with self.assertNumQueries(FuzzyInt(8, 13)):
                response = self.client.get('/en/')
                resp2 = response.content.decode('utf8').split("$$$")[1]
        self.assertNotEqual(output, output2)
        self.assertNotEqual(resp1, resp2)

        plugin_pool.unregister_plugin(NoCachePlugin)

    def test_cache_page(self):
        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware'
        ]
        mw_classes = [mw for mw in settings.MIDDLEWARE_CLASSES if mw not in exclude]

        with self.settings(MIDDLEWARE_CLASSES=mw_classes):

            # Silly to do these tests if this setting isn't True
            page_cache_setting = get_cms_setting('PAGE_CACHE')
            self.assertTrue(page_cache_setting)

            # Create a test page
            page1 = create_page('test page 1', 'nav_playground.html', 'en', published=True)

            # Add some content
            placeholder = page1.placeholders.filter(slot="body")[0]
            add_plugin(placeholder, "TextPlugin", 'en', body="English")
            add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")

            # Create a request object
            request = self.get_request(page1.get_path(), 'en')

            # Ensure that user is NOT authenticated
            self.assertFalse(request.user.is_authenticated())

            # Test that the page is initially uncached
            with self.assertNumQueries(FuzzyInt(1, 22)):
                response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)

            #
            # Test that subsequent requests of the same page are cached by
            # asserting that they require fewer queries.
            #
            with self.assertNumQueries(0):
                response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)

            #
            # Test that the cache is invalidated on unpublishing the page
            #
            old_version = _get_cache_version()
            page1.unpublish('en')
            self.assertGreater(_get_cache_version(), old_version)

            #
            # Test that this means the page is actually not cached.
            #
            page1.publish('en')
            with self.assertNumQueries(FuzzyInt(1, 20)):
                response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)

            #
            # Test that the above behavior is different when CMS_PAGE_CACHE is
            # set to False (disabled)
            #
            with self.settings(CMS_PAGE_CACHE=False):


                # Test that the page is initially uncached
                with self.assertNumQueries(FuzzyInt(1, 20)):
                    response = self.client.get('/en/')
                self.assertEqual(response.status_code, 200)

                #
                # Test that subsequent requests of the same page are still requires DB
                # access.
                #
                with self.assertNumQueries(FuzzyInt(1, 20)):
                    response = self.client.get('/en/')
                self.assertEqual(response.status_code, 200)

    def test_invalidate_restart(self):

        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware'
        ]
        mw_classes = [mw for mw in settings.MIDDLEWARE_CLASSES if mw not in exclude]

        with self.settings(MIDDLEWARE_CLASSES=mw_classes):

            # Silly to do these tests if this setting isn't True
            page_cache_setting = get_cms_setting('PAGE_CACHE')
            self.assertTrue(page_cache_setting)

            # Create a test page
            page1 = create_page('test page 1', 'nav_playground.html', 'en', published=True)

            # Add some content
            placeholder = page1.placeholders.filter(slot="body")[0]
            add_plugin(placeholder, "TextPlugin", 'en', body="English")
            add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")

            # Create a request object
            request = self.get_request(page1.get_path(), 'en')

            # Ensure that user is NOT authenticated
            self.assertFalse(request.user.is_authenticated())

            # Test that the page is initially uncached
            with self.assertNumQueries(FuzzyInt(1, 20)):
                response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)

            #
            # Test that subsequent requests of the same page are cached by
            # asserting that they require fewer queries.
            #
            with self.assertNumQueries(0):
                response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)
            old_plugins = plugin_pool.plugins
            plugin_pool.clear()
            plugin_pool.discover_plugins()
            plugin_pool.plugins = old_plugins
            with self.assertNumQueries(FuzzyInt(1, 20)):
                response = self.client.get('/en/')
                self.assertEqual(response.status_code, 200)

    def test_sekizai_plugin(self):
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)

        placeholder1 = page1.placeholders.filter(slot="body")[0]
        placeholder2 = page1.placeholders.filter(slot="right-column")[0]
        plugin_pool.register_plugin(SekizaiPlugin)
        add_plugin(placeholder1, "SekizaiPlugin", 'en')
        add_plugin(placeholder2, "TextPlugin", 'en', body="Deutsch")
        page1.publish('en')
        response = self.client.get('/en/')
        self.assertContains(response, 'alert(')
        response = self.client.get('/en/')
        self.assertContains(response, 'alert(')

    def test_cache_invalidation(self):

        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware'
        ]
        mw_classes = [mw for mw in settings.MIDDLEWARE_CLASSES if mw not in exclude]

        with self.settings(MIDDLEWARE_CLASSES=mw_classes):
            # Silly to do these tests if this setting isn't True
            page_cache_setting = get_cms_setting('PAGE_CACHE')
            self.assertTrue(page_cache_setting)
            page1 = create_page('test page 1', 'nav_playground.html', 'en',
                                published=True)

            placeholder = page1.placeholders.get(slot="body")
            add_plugin(placeholder, "TextPlugin", 'en', body="First content")
            page1.publish('en')
            response = self.client.get('/en/')
            self.assertContains(response, 'First content')
            response = self.client.get('/en/')
            self.assertContains(response, 'First content')
            add_plugin(placeholder, "TextPlugin", 'en', body="Second content")
            page1.publish('en')
            response = self.client.get('/en/')
            self.assertContains(response, 'Second content')

    def test_render_placeholder_cache(self):
        """
        Regression test for #4223

        Assert that placeholder cache is cleared correctly when a plugin is saved
        """
        invalidate_cms_page_cache()
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
        ##
        test_plugin = add_plugin(ph1, u"TextPlugin", u"en", body="Some text")
        test_plugin.save()

        # asserting initial text
        context = SekizaiContext()
        context['request'] = self.get_request()
        text = render_placeholder(ph1, context)
        self.assertEqual(text, "Some text")

        # deleting local plugin cache
        del ph1._plugins_cache
        test_plugin.body = 'Other text'
        test_plugin.save()

        # plugin text has changed, so the placeholder rendering
        text = render_placeholder(ph1, context)
        self.assertEqual(text, "Other text")
