import time

from django.conf import settings
from django.template import Context
from sekizai.context import SekizaiContext

from cms.api import add_plugin, create_page, create_page_content
from cms.cache import invalidate_cms_page_cache
from cms.cache.placeholder import (
    _get_placeholder_cache_key,
    _get_placeholder_cache_version,
    _get_placeholder_cache_version_key,
    _set_placeholder_cache_version,
    clear_placeholder_cache,
    get_placeholder_cache,
    set_placeholder_cache,
)
from cms.exceptions import PluginAlreadyRegistered
from cms.models import Page
from cms.plugin_pool import plugin_pool
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.project.pluginapp.plugins.caching.cms_plugins import (
    DateTimeCacheExpirationPlugin,
    LegacyCachePlugin,
    NoCachePlugin,
    SekizaiPlugin,
    TimeDeltaCacheExpirationPlugin,
    TTLCacheExpirationPlugin,
    VaryCacheOnPlugin,
)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar.utils import get_object_edit_url
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import get_timezone_name


class CacheTestCase(CMSTestCase):
    def tearDown(self):
        from django.core.cache import cache

        super().tearDown()
        cache.clear()

    def setUp(self):
        from django.core.cache import cache

        super().setUp()
        cache.clear()

    def test_cache_placeholder(self):
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        page1 = create_page("test page 1", "nav_playground.html", "en")
        page1_url = page1.get_absolute_url()

        placeholder_en = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder_de = page1.get_placeholders("en").filter(slot="body")[0]
        add_plugin(placeholder_en, "TextPlugin", "en", body="English")
        add_plugin(placeholder_de, "TextPlugin", "de", body="Deutsch")
        request = self.get_request(page1_url)
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        with self.assertNumQueries(FuzzyInt(4, 8)):
            self.render_template_obj(template, {}, request)
        request = self.get_request(page1_url)
        request.session["cms_edit"] = True
        request.current_page = Page.objects.get(pk=page1.pk)
        request.toolbar = CMSToolbar(request)
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(2):
            self.render_template_obj(template, {}, request)
        # toolbar
        with self.login_user_context(self.get_superuser()):
            request = self.get_request(page1_url)
            request.session["cms_edit"] = True
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            request.toolbar.show_toolbar = True
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"
        with self.assertNumQueries(4):
            self.render_template_obj(template, {}, request)
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = dict(
            CMS_PAGE_CACHE=False,
            MIDDLEWARE=[mw for mw in settings.MIDDLEWARE if mw not in exclude],
        )
        with self.settings(**overrides):
            with self.assertNumQueries(FuzzyInt(13, 25)):
                self.client.get(page1_url)
            with self.assertNumQueries(FuzzyInt(5, 13)):
                self.client.get(page1_url)

        overrides["CMS_PLACEHOLDER_CACHE"] = False
        with self.settings(**overrides):
            with self.assertNumQueries(FuzzyInt(7, 17)):
                self.client.get(page1_url)

    def test_no_cache_plugin(self):
        page1 = create_page("test page 1", "nav_playground.html", "en")
        page1_url = page1.get_absolute_url()

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        try:
            plugin_pool.register_plugin(NoCachePlugin)
        except PluginAlreadyRegistered:
            pass
        add_plugin(placeholder1, "TextPlugin", "en", body="English")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")
        template = "{% load cms_tags %}{% placeholder 'body' %}{% placeholder 'right-column' %}"

        # Ensure that we're testing in an environment WITHOUT the MW cache, as
        # we are testing the internal page cache, not the MW cache.
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.CacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            # Request the page without the 'no-cache' plugin
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(16, 23)):
                response1 = self.client.get(page1_url)
                content1 = response1.content

            # Fetch it again, it is cached.
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(0):
                response2 = self.client.get(page1_url)
                content2 = response2.content
            self.assertEqual(content1, content2)

            # Once again with PAGE_CACHE=False, to prove the cache can
            # be disabled
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.settings(CMS_PAGE_CACHE=False):
                with self.assertNumQueries(FuzzyInt(5, 24)):
                    response3 = self.client.get(page1_url)
                    content3 = response3.content
            self.assertEqual(content1, content3)

            # Add the 'no-cache' plugin
            with self.login_user_context(self.get_superuser()):
                endpoint = self.get_add_plugin_uri(placeholder1, "NoCachePlugin")
                self.client.post(endpoint, {})
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(4, 6)):
                output = self.render_template_obj(template, {}, request)
            with self.assertNumQueries(FuzzyInt(13, 24)):
                response = self.client.get(page1_url)
                self.assertTrue("no-cache" in response["Cache-Control"])
                resp1 = response.content.decode("utf8").split("$$$")[1]

            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(5):
                output2 = self.render_template_obj(template, {}, request)
            with self.settings(CMS_PAGE_CACHE=False):
                with self.assertNumQueries(FuzzyInt(8, 16)):
                    response = self.client.get(page1_url)
                    resp2 = response.content.decode("utf8").split("$$$")[1]
            self.assertNotEqual(output, output2)
            self.assertNotEqual(resp1, resp2)

        plugin_pool.unregister_plugin(NoCachePlugin)

    def test_timedelta_cache_plugin(self):
        page1 = create_page("test page 1", "nav_playground.html", "en")

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        plugin_pool.register_plugin(TimeDeltaCacheExpirationPlugin)
        add_plugin(placeholder1, "TextPlugin", "en", body="English")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")

        # Add *TimeDeltaCacheExpirationPlugin, expires in 45s.
        add_plugin(placeholder1, "TimeDeltaCacheExpirationPlugin", "en")

        # Ensure that we're testing in an environment WITHOUT the MW cache, as
        # we are testing the internal page cache, not the MW cache.
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.CacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            request = self.get_request(page1.get_absolute_url())
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(14, 25)):  # was 14, 24
                response = self.client.get(page1.get_absolute_url())

            self.assertTrue(
                "max-age=45" in response["Cache-Control"], response["Cache-Control"]
            )

        plugin_pool.unregister_plugin(TimeDeltaCacheExpirationPlugin)

    def test_datetime_cache_plugin(self):
        page1 = create_page("test page 1", "nav_playground.html", "en")
        page1_url = page1.get_absolute_url()

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        try:
            plugin_pool.register_plugin(DateTimeCacheExpirationPlugin)
        except PluginAlreadyRegistered:
            pass
        add_plugin(placeholder1, "TextPlugin", "en", body="English")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")

        # Add *CacheExpirationPlugins, one expires in 50s, the other in 40s.
        # The page should expire in the least of these, or 40s.
        add_plugin(placeholder1, "DateTimeCacheExpirationPlugin", "en")

        # Ensure that we're testing in an environment WITHOUT the MW cache, as
        # we are testing the internal page cache, not the MW cache.
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.CacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(14, 25)):  # was 14, 24
                response = self.client.get(page1_url)
            self.assertTrue(
                "max-age=40" in response["Cache-Control"], response["Cache-Control"]
            )

        plugin_pool.unregister_plugin(DateTimeCacheExpirationPlugin)

    def TTLCacheExpirationPlugin(self):
        page1 = create_page("test page 1", "nav_playground.html", "en")

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        plugin_pool.register_plugin(TTLCacheExpirationPlugin)
        add_plugin(placeholder1, "TextPlugin", "en", body="English")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")

        # Add *CacheExpirationPlugins, one expires in 50s, the other in 40s.
        # The page should expire in the least of these, or 40s.
        add_plugin(placeholder1, "TTLCacheExpirationPlugin", "en")

        # Ensure that we're testing in an environment WITHOUT the MW cache, as
        # we are testing the internal page cache, not the MW cache.
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.CacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            request = self.get_request("/en/")
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(14, 25)):  # was 14, 24
                response = self.client.get("/en/")
            self.assertTrue(
                "max-age=50" in response["Cache-Control"], response["Cache-Control"]
            )

            plugin_pool.unregister_plugin(TTLCacheExpirationPlugin)

    def test_expiration_cache_plugins(self):
        """
        Tests that when used in combination, the page is cached to the
        shortest TTL.
        """
        page1 = create_page("test page 1", "nav_playground.html", "en")
        page1_url = page1.get_absolute_url()

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        plugin_pool.register_plugin(TTLCacheExpirationPlugin)
        try:
            plugin_pool.register_plugin(DateTimeCacheExpirationPlugin)
        except PluginAlreadyRegistered:
            pass
        try:
            plugin_pool.register_plugin(NoCachePlugin)
        except PluginAlreadyRegistered:
            pass
        add_plugin(placeholder1, "TextPlugin", "en", body="English")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")

        # Add *CacheExpirationPlugins, one expires in 50s, the other in 40s.
        # The page should expire in the least of these, or 40s.
        add_plugin(placeholder1, "TTLCacheExpirationPlugin", "en")
        add_plugin(placeholder2, "DateTimeCacheExpirationPlugin", "en")

        # Ensure that we're testing in an environment WITHOUT the MW cache, as
        # we are testing the internal page cache, not the MW cache.
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.CacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(14, 26)):
                response = self.client.get(page1_url)
                resp1 = response.content.decode("utf8").split("$$$")[1]
            self.assertTrue(
                "max-age=40" in response["Cache-Control"], response["Cache-Control"]
            )  # noqa
            cache_control1 = response["Cache-Control"]
            expires1 = response["Expires"]

            time.sleep(1)  # This ensures that the cache has aged measurably

            # Request it again, this time, it comes from the cache
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(0):
                response = self.client.get(page1_url)
                resp2 = response.content.decode("utf8").split("$$$")[1]
            # Content will be the same
            self.assertEqual(resp2, resp1)
            # Cache-Control will be different because the cache has aged
            self.assertNotEqual(response["Cache-Control"], cache_control1)
            # However, the Expires timestamp will be the same
            self.assertEqual(response["Expires"], expires1)

        plugin_pool.unregister_plugin(TTLCacheExpirationPlugin)
        plugin_pool.unregister_plugin(DateTimeCacheExpirationPlugin)
        plugin_pool.unregister_plugin(NoCachePlugin)

    def test_dual_legacy_cache_plugins(self):
        page1 = create_page("test page 1", "nav_playground.html", "en")
        page1_url = page1.get_absolute_url()

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        plugin_pool.register_plugin(LegacyCachePlugin)
        add_plugin(placeholder1, "TextPlugin", "en", body="English")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")
        # Adds a no-cache plugin. In older versions of the CMS, this would
        # prevent the page from caching in, but since this plugin also defines
        # get_cache_expiration() it is ignored.
        add_plugin(placeholder1, "LegacyCachePlugin", "en")
        # Ensure that we're testing in an environment WITHOUT the MW cache, as
        # we are testing the internal page cache, not the MW cache.
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.CacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            request = self.get_request(page1_url)
            request.current_page = Page.objects.get(pk=page1.pk)
            request.toolbar = CMSToolbar(request)
            with self.assertNumQueries(FuzzyInt(14, 25)):
                response = self.client.get(page1_url)
            self.assertTrue("no-cache" not in response["Cache-Control"])

        plugin_pool.unregister_plugin(LegacyCachePlugin)

    def test_cache_page(self):
        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):

            # Silly to do these tests if this setting isn't True
            page_cache_setting = get_cms_setting("PAGE_CACHE")
            self.assertTrue(page_cache_setting)

            # Create a test page
            page1 = create_page("test page 1", "nav_playground.html", "en")
            page1_url = page1.get_absolute_url()

            # Add some content
            placeholder = page1.get_placeholders("en").filter(slot="body")[0]
            add_plugin(placeholder, "TextPlugin", "en", body="English")
            add_plugin(placeholder, "TextPlugin", "de", body="Deutsch")

            # Create a request object
            request = self.get_request(page1_url, "en")

            # Ensure that user is NOT authenticated
            self.assertFalse(request.user.is_authenticated)

            # Test that the page is initially uncached
            with self.assertNumQueries(FuzzyInt(1, 25)):
                response = self.client.get(page1_url)
            self.assertEqual(response.status_code, 200)

            #
            # Test that subsequent requests of the same page are cached by
            # asserting that they require fewer queries.
            #
            with self.assertNumQueries(0):
                response = self.client.get(page1_url)
            self.assertEqual(response.status_code, 200)

            # Test that the above behavior is different when CMS_PAGE_CACHE is
            # set to False (disabled)
            with self.settings(CMS_PAGE_CACHE=False):

                # Test that the page is initially un-cached
                with self.assertNumQueries(FuzzyInt(1, 20)):
                    response = self.client.get(page1_url)
                self.assertEqual(response.status_code, 200)

                #
                # Test that subsequent requests of the same page are still requires DB
                # access.
                #
                with self.assertNumQueries(FuzzyInt(1, 20)):
                    response = self.client.get(page1_url)
                self.assertEqual(response.status_code, 200)

    def test_no_page_cache_on_toolbar_edit(self):
        with self.settings(CMS_PAGE_CACHE=True):
            superuser = self.get_superuser()
            # Create a test page
            page = create_page("test page 1", "nav_playground.html", "en")
            page_content = self.get_pagecontent_obj(page)
            page_url = page.get_absolute_url()
            page_edit_url = get_object_edit_url(page_content)

            # Add some content
            placeholder = page.get_placeholders("en").filter(slot="body")[0]
            add_plugin(placeholder, "TextPlugin", "en", body="English")
            add_plugin(placeholder, "TextPlugin", "de", body="Deutsch")

            # Make an initial edit endpoint request
            with self.login_user_context(superuser):
                with self.assertNumQueries(FuzzyInt(1, 35)):
                    response = self.client.get(page_edit_url)
            self.assertEqual(response.status_code, 200)

            # Set the cache
            with self.assertNumQueries(FuzzyInt(1, 24)):
                response = self.client.get(page_url)
            self.assertEqual(response.status_code, 200)

            # Assert cached content was used
            with self.assertNumQueries(0):
                response = self.client.get(page_url)
            self.assertEqual(response.status_code, 200)

    def test_invalidate_restart(self):

        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):

            # Silly to do these tests if this setting isn't True
            page_cache_setting = get_cms_setting("PAGE_CACHE")
            self.assertTrue(page_cache_setting)

            # Create a test page
            page1 = create_page("test page 1", "nav_playground.html", "en")
            page1_url = page1.get_absolute_url()

            # Add some content
            placeholder = page1.get_placeholders("en").filter(slot="body")[0]
            add_plugin(placeholder, "TextPlugin", "en", body="English")
            add_plugin(placeholder, "TextPlugin", "de", body="Deutsch")

            # Create a request object
            request = self.get_request(page1.get_path("en"), "en")

            # Ensure that user is NOT authenticated
            self.assertFalse(request.user.is_authenticated)

            # Test that the page is initially uncached
            with self.assertNumQueries(FuzzyInt(1, 25)):
                response = self.client.get(page1_url)
            self.assertEqual(response.status_code, 200)

            #
            # Test that subsequent requests of the same page are cached by
            # asserting that they require fewer queries.
            #
            with self.assertNumQueries(0):
                response = self.client.get(page1_url)
            self.assertEqual(response.status_code, 200)
            old_plugins = plugin_pool.plugins
            plugin_pool.clear()
            plugin_pool.discover_plugins()
            plugin_pool.plugins = old_plugins
            with self.assertNumQueries(FuzzyInt(1, 20)):
                response = self.client.get(page1_url)
                self.assertEqual(response.status_code, 200)

    def test_sekizai_plugin(self):
        page1 = create_page("test page 1", "nav_playground.html", "en")

        placeholder1 = page1.get_placeholders("en").filter(slot="body")[0]
        placeholder2 = page1.get_placeholders("en").filter(slot="right-column")[0]
        plugin_pool.register_plugin(SekizaiPlugin)
        add_plugin(placeholder1, "SekizaiPlugin", "en")
        add_plugin(placeholder2, "TextPlugin", "en", body="Deutsch")
        response = self.client.get(page1.get_absolute_url())
        self.assertContains(response, "alert(")
        response = self.client.get(page1.get_absolute_url())
        self.assertContains(response, "alert(")

    def test_cache_invalidation(self):

        # Ensure that we're testing in an environment WITHOUT the MW cache...
        exclude = [
            "django.middleware.cache.UpdateCacheMiddleware",
            "django.middleware.cache.FetchFromCacheMiddleware",
        ]
        overrides = {
            "MIDDLEWARE": [mw for mw in settings.MIDDLEWARE if mw not in exclude]
        }
        with self.settings(**overrides):
            # Silly to do these tests if this setting isn't True
            page_cache_setting = get_cms_setting("PAGE_CACHE")
            self.assertTrue(page_cache_setting)
            page1 = create_page("test page 1", "nav_playground.html", "en")
            page1_url = page1.get_absolute_url()

            placeholder = page1.get_placeholders("en").get(slot="body")
            add_plugin(placeholder, "TextPlugin", "en", body="First content")
            response = self.client.get(page1_url)
            self.assertContains(response, "First content")
            response = self.client.get(page1_url)
            self.assertContains(response, "First content")

            with self.login_user_context(self.get_superuser()):
                post_data = {
                    "name": "A Link",
                    "external_link": "https://www.django-cms.org",
                }
                endpoint = self.get_add_plugin_uri(placeholder, "LinkPlugin")
                self.client.post(endpoint, post_data)
            response = self.client.get(page1_url)
            self.assertContains(response, "A Link")

    def test_render_placeholder_cache(self):
        """
        Regression test for #4223

        Assert that placeholder cache is cleared correctly when a plugin is saved
        """
        invalidate_cms_page_cache()
        ex = Example1(char_1="one", char_2="two", char_3="tree", char_4="four")
        ex.save()
        ph1 = ex.placeholder
        ###
        # add the test plugin
        ##
        test_plugin = add_plugin(ph1, "TextPlugin", "en", body="Some text")
        test_plugin.save()

        request = self.get_request()
        content_renderer = self.get_content_renderer(request)
        # asserting initial text
        context = SekizaiContext()
        context["request"] = self.get_request()
        text = content_renderer.render_placeholder(ph1, context)
        self.assertEqual(text, "Some text")

        # deleting local plugin cache
        del ph1._plugins_cache
        test_plugin.body = "Other text"
        test_plugin.save()

        # plugin text has changed, so the placeholder rendering
        text = content_renderer.render_placeholder(ph1, context)
        self.assertEqual(text, "Other text")


class PlaceholderCacheTestCase(CMSTestCase):
    def setUp(self):
        from django.core.cache import cache

        super().setUp()
        cache.clear()

        self.page = create_page("en test page", "nav_playground.html", "en")
        # Now create and publish as 'de' title
        create_page_content(
            "de", "de test page", self.page, template="nav_playground.html"
        )

        self.placeholder_en = self.page.get_placeholders("en").filter(slot="body")[0]
        self.placeholder_de = self.page.get_placeholders("de").filter(slot="body")[0]
        plugin_pool.register_plugin(VaryCacheOnPlugin)
        add_plugin(self.placeholder_en, "TextPlugin", "en", body="English")
        add_plugin(self.placeholder_de, "TextPlugin", "de", body="Deutsch")
        add_plugin(self.placeholder_en, "VaryCacheOnPlugin", "en")
        add_plugin(self.placeholder_de, "VaryCacheOnPlugin", "de")

        self.en_request = self.get_request("/en/")
        self.en_request.current_page = Page.objects.get(pk=self.page.pk)

        self.en_us_request = self.get_request("/en/")
        self.en_us_request.META["HTTP_COUNTRY_CODE"] = "US"

        self.en_uk_request = self.get_request("/en/")
        self.en_uk_request.META["HTTP_COUNTRY_CODE"] = "UK"

        self.de_request = self.get_request("/de/")
        self.de_request.current_page = Page.objects.get(pk=self.page.pk)

    def tearDown(self):
        from django.core.cache import cache

        super().tearDown()
        plugin_pool.unregister_plugin(VaryCacheOnPlugin)
        cache.clear()

    def test_get_placeholder_cache_version_key(self):
        cache_version_key = (
            "{prefix}|placeholder_cache_version|id:{id}|lang:{lang}|site:{site}".format(
                prefix=get_cms_setting("CACHE_PREFIX"),
                id=self.placeholder_en.pk,
                lang="en",
                site=1,
            )
        )
        self.assertEqual(
            _get_placeholder_cache_version_key(self.placeholder_en, "en", 1),
            cache_version_key,
        )

    def test_set_clear_get_placeholder_cache_version(self):
        initial, _ = _get_placeholder_cache_version(self.placeholder_en, "en", 1)
        clear_placeholder_cache(self.placeholder_en, "en", 1)
        version, _ = _get_placeholder_cache_version(self.placeholder_en, "en", 1)
        self.assertGreater(version, initial)

    def test_get_placeholder_cache_key(self):
        version, vary_on_list = _get_placeholder_cache_version(
            self.placeholder_en, "en", 1
        )
        desired_key = "{prefix}|render_placeholder|id:{id}|lang:{lang}|site:{site}|tz:{tz}|v:{version}|country-code:{cc}".format(  # noqa
            prefix=get_cms_setting("CACHE_PREFIX"),
            id=self.placeholder_en.pk,
            lang="en",
            site=1,
            tz=get_timezone_name(),
            version=version,
            cc="_",
        )
        _set_placeholder_cache_version(
            self.placeholder_en, "en", 1, version, vary_on_list=vary_on_list, duration=1
        )
        actual_key = _get_placeholder_cache_key(
            self.placeholder_en, "en", 1, self.en_request
        )
        self.assertEqual(actual_key, desired_key)

        en_key = _get_placeholder_cache_key(
            self.placeholder_en, "en", 1, self.en_request
        )
        de_key = _get_placeholder_cache_key(
            self.placeholder_de, "de", 1, self.de_request
        )
        self.assertNotEqual(en_key, de_key)

        en_us_key = _get_placeholder_cache_key(
            self.placeholder_en, "en", 1, self.en_us_request
        )
        self.assertNotEqual(en_key, en_us_key)

        desired_key = "{prefix}|render_placeholder|id:{id}|lang:{lang}|site:{site}|tz:{tz}|v:{version}|country-code:{cc}".format(  # noqa
            prefix=get_cms_setting("CACHE_PREFIX"),
            id=self.placeholder_en.pk,
            lang="en",
            site=1,
            tz=get_timezone_name(),
            version=version,
            cc="US",
        )
        self.assertEqual(en_us_key, desired_key)

    def test_set_get_placeholder_cache(self):
        # Test with a super-long prefix
        en_renderer = self.get_content_renderer(self.en_request)
        en_context = Context(
            {
                "request": self.en_request,
            }
        )
        en_us_renderer = self.get_content_renderer(self.en_us_request)
        en_us_context = Context(
            {
                "request": self.en_us_request,
            }
        )
        en_uk_renderer = self.get_content_renderer(self.en_uk_request)
        en_uk_context = Context(
            {
                "request": self.en_uk_request,
            }
        )

        en_content = en_renderer.render_placeholder(
            self.placeholder_en, en_context, "en", width=350
        )
        en_us_content = en_us_renderer.render_placeholder(
            self.placeholder_en, en_us_context, "en", width=350
        )
        en_uk_content = en_uk_renderer.render_placeholder(
            self.placeholder_en, en_uk_context, "en", width=350
        )

        del self.placeholder_en._plugins_cache

        de_renderer = self.get_content_renderer(self.de_request)
        de_context = Context(
            {
                "request": self.de_request,
            }
        )
        de_content = de_renderer.render_placeholder(
            self.placeholder_de, de_context, "de", width=350
        )

        self.assertNotEqual(en_content, de_content)

        set_placeholder_cache(self.placeholder_en, "en", 1, en_content, self.en_request)
        cached_en_content = get_placeholder_cache(
            self.placeholder_en, "en", 1, self.en_request
        )
        self.assertEqual(cached_en_content, en_content)

        set_placeholder_cache(self.placeholder_de, "de", 1, de_content, self.de_request)
        cached_de_content = get_placeholder_cache(
            self.placeholder_de, "de", 1, self.de_request
        )
        self.assertNotEqual(cached_en_content, cached_de_content)

        set_placeholder_cache(
            self.placeholder_en, "en", 1, en_us_content, self.en_us_request
        )
        cached_en_us_content = get_placeholder_cache(
            self.placeholder_en, "en", 1, self.en_us_request
        )
        self.assertNotEqual(cached_en_content, cached_en_us_content)

        set_placeholder_cache(
            self.placeholder_en, "en", 1, en_uk_content, self.en_uk_request
        )
        cached_en_uk_content = get_placeholder_cache(
            self.placeholder_en, "en", 1, self.en_uk_request
        )
        self.assertNotEqual(cached_en_us_content, cached_en_uk_content)

    def test_set_get_placeholder_cache_with_long_prefix(self):
        """
        This is for testing that everything continues to work even when the
        cache-keys are hashed.
        """
        # Use an absurdly long cache prefix to get us in the right neighborhood...
        with self.settings(CMS_CACHE_PREFIX="super_lengthy_prefix" * 9):  # 180 chars
            en_crazy_request = self.get_request("/en/")
            en_crazy_renderer = self.get_content_renderer(self.de_request)
            # Use a ridiculously long "country code" (80 chars), already we're at 260 chars.
            en_crazy_request.META["HTTP_COUNTRY_CODE"] = "US" * 40  # 80 chars
            en_crazy_context = Context({"request": en_crazy_request})
            en_crazy_content = en_crazy_renderer.render_placeholder(
                self.placeholder_en,
                en_crazy_context,
                language="en",
                width=350,
            )
            set_placeholder_cache(
                self.placeholder_en, "en", 1, en_crazy_content, en_crazy_request
            )

            # Prove that it is hashed...
            crazy_cache_key = _get_placeholder_cache_key(
                self.placeholder_en, "en", 1, en_crazy_request
            )
            key_length = len(crazy_cache_key)
            # 221 = 180 (prefix length) + 1 (separator) + 40 (sha1 hash)
            self.assertTrue(
                "render_placeholder" not in crazy_cache_key and key_length == 221
            )

            # Prove it still works as expected
            cached_en_crazy_content = get_placeholder_cache(
                self.placeholder_en, "en", 1, en_crazy_request
            )
            self.assertEqual(en_crazy_content, cached_en_crazy_content)
