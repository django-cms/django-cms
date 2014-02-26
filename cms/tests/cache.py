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
        from django.conf import settings
        from cms.views import details, _get_cache_version
        from cms.utils import get_cms_setting
        from django import db


        # Silly to do these tests if this setting isn't True
        page_cache_setting = get_cms_setting('PAGE_CACHE')
        self.assertTrue(page_cache_setting)

        settings.CMS_PAGE_CACHE=False

        # Create a test page
        page1 = create_page('test page 1', 'nav_playground.html', 'en', published=True)

        # Add some content
        placeholder = page1.placeholders.filter(slot="body")[0]
        add_plugin(placeholder, "TextPlugin", 'en', body="English")
        add_plugin(placeholder, "TextPlugin", 'de', body="Deutsch")

        # Create a request object
        request = self.get_request(page1.get_path(), 'en')

        # Test that the page is initially uncached
        db.reset_queries()
        with self.assertNumQueries(FuzzyInt(4, 10)):
            response = details(request, page1.get_path())
        print('Initial request:')
        print(db.connection.queries)

        # Test it was actually a valid page response and not a 302 or 404 or other
        self.assertEqual(response.status_code, 200)

        #
        # Test that subsequent requests of the same page are cached by
        # asserting that they require fewer queries.
        #
        db.reset_queries()
        with self.assertNumQueries(FuzzyInt(0, 2)):
            response = details(request, page1.get_path())
        print('Subsequent (cached) request:')
        print(db.connection.queries)

        # Test it was actually a valid page response
        self.assertEqual(response.status_code, 200)

        # Test that the cache is invalidated on unpublishing the page
        old_version = _get_cache_version()
        page1.unpublish('en')
        self.assertGreater(_get_cache_version(), old_version)

        cache.clear() # WTF? How can this not force us to use more queries?!?

        # Test that this means the page is actually not cached
        page1.publish('en')
        db.reset_queries()
        with self.assertNumQueries(FuzzyInt(4, 10)):
            response = details(request, page1.get_path())
        print('Post re-published request:')
        print(db.connection.queries)

        # Test it was actually a valid page response
        self.assertEqual(response.status_code, 200)
