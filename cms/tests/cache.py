# -*- coding: utf-8 -*-
from cms.api import add_plugin, create_page
from cms.models import Page
from cms.plugin_pool import plugin_pool
from cms.test_utils.project.pluginapp.plugins.caching.cms_plugins import NoCachePlugin
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.toolbar import CMSToolbar
from django.core.cache import cache
from django.db import connection
from django.template import Template, RequestContext


class CacheTestCase(CMSTestCase):
    def tearDown(self):
        cache.clear()

    def test_cache_placeholder(self):
        create_page
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)

        placeholder = page1.placeholders.filter(slot="body")[0]
        add_plugin(placeholder, "TextPlugin", 'en', body="English")
        add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        rctx = RequestContext(request)
        with self.assertNumQueries(3):
            template.render(rctx)
        connection.queries = []
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        request.toolbar.edit_mode = False
        rctx = RequestContext(request)
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        with self.assertNumQueries(1):
            template.render(rctx)
        # toolbar
        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        request.toolbar.edit_mode = True
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        rctx = RequestContext(request)
        with self.assertNumQueries(3):
            template.render(rctx)

    def test_no_cache_plugin(self):
        create_page
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
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
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        rctx = RequestContext(request)
        with self.assertNumQueries(3):
            template.render(rctx)

        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        rctx = RequestContext(request)
        with self.assertNumQueries(1):
            template.render(rctx)
        add_plugin(placeholder1, "NoCachePlugin", 'en')

        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        rctx = RequestContext(request)
        with self.assertNumQueries(4):
            template.render(rctx)

        request = self.get_request('/en/')
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = Template("{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}")
        rctx = RequestContext(request)
        with self.assertNumQueries(4):
            template.render(rctx)

        plugin_pool.unregister_plugin(NoCachePlugin)


    def test_cache_page(self):
        from cms.views import _get_cache_version
        from cms.utils import get_cms_setting

        from django.conf import settings

        # We'll store the old MW so that we can play nice with the other tests
        old_middleware = settings.MIDDLEWARE_CLASSES[:]

        # Clear the entire cache for a clean slate
        cache.clear()

        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware'
        ]
        settings.MIDDLEWARE_CLASSES[:] = [mw for mw in settings.MIDDLEWARE_CLASSES if mw not in exclude]

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
        cache.clear()
        settings.CMS_PAGE_CACHE = False

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

        #
        # Let's reset the original middleware for the remaining tests...
        #
        settings.MIDDLEWARE_CLASSES = old_middleware[:]
