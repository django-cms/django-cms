# -*- coding: utf-8 -*-
from cms.api import add_plugin, create_page
from cms.models import Page
from cms.plugin_pool import plugin_pool
from cms.test_utils.project.pluginapp.plugins.caching.cms_plugins import NoCachePlugin
from cms.test_utils.testcases import CMSTestCase
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