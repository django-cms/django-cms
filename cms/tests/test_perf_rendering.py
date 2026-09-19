"""
Performance regression tests for the public render path.

Each test documents one finding of the performance audit (ID in the
docstring) and asserts on the specific symptom, not on total query counts.
"""
import gc
import re
import weakref
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.db.models import Value
from django.utils.module_loading import import_string

from cms import constants
from cms.api import add_plugin, create_page
from cms.models import Page, PageContent
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.test_utils.project.pluginapp.plugins.caching.cms_plugins import NoCachePlugin
from cms.test_utils.project.pluginapp.plugins.link.cms_plugins import LinkPlugin
from cms.test_utils.project.pluginapp.plugins.link.models import Link
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.perf import capture_queries, queries_on
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.plugins import assign_plugins

# Django's own cache middleware would hide the CMS page cache.
DJANGO_CACHE_MIDDLEWARE = (
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
)
MIDDLEWARE_NO_DJANGO_CACHE = [mw for mw in settings.MIDDLEWARE if mw not in DJANGO_CACHE_MIDDLEWARE]

# An address the test client never uses, so every request is "external".
INTERNAL_IPS_ELSEWHERE = ["10.255.255.1"]

SELECT_LIST = re.compile(r"^SELECT .*? FROM")

PLUGIN_PROCESSOR = "cms.tests.test_perf_rendering.perf_plugin_processor"
CONTEXT_PROCESSOR = "cms.tests.test_perf_rendering.perf_context_processor"


def perf_plugin_processor(instance, placeholder, rendered_content, original_context):
    return rendered_content


def perf_context_processor(instance, placeholder, original_context):
    return {}


class PerfTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def _brief(self, statements):
        # Drop the column lists: failure messages stay readable.
        return [SELECT_LIST.sub("SELECT ... FROM", sql, count=1) for sql in statements]

    def _fresh_page(self, page):
        # A new instance, like the one a request gets: no cached relations.
        return Page.objects.get(pk=page.pk)

    def _anon_request(self, page, with_toolbar=True):
        request = self.get_request(page.get_absolute_url("en"))
        request.current_page = self._fresh_page(page)

        if with_toolbar:
            # What ``ToolbarMiddleware`` does for a regular CMS request.
            request.toolbar = CMSToolbar(request)
        return request


class MissingToolbarTests(PerfTestCase):
    def test_p1_placeholders_once(self):
        """P1: without ``request.toolbar``, tags must share one renderer."""
        page = create_page("page", "col_two.html", "en")

        for slot in ("col_sidebar", "col_left"):
            add_plugin(page.get_placeholders("en").get(slot=slot), "LinkPlugin", "en", name="a")

        # No toolbar middleware ran: ``request.toolbar`` is missing.
        request = self._anon_request(page, with_toolbar=False)
        self.assertFalse(hasattr(request, "toolbar"))
        template = "{% load cms_tags %}{% placeholder 'col_sidebar' %}{% placeholder 'col_left' %}"

        with capture_queries() as captured:
            self.render_template_obj(template, {}, request)

        # All placeholders of the page are preloaded by the first tag;
        # the second tag must not load them again.
        placeholder_queries = queries_on(captured, "cms_placeholder")
        self.assertEqual(len(placeholder_queries), 1, self._brief(placeholder_queries))

    def test_p1_page_is_cached(self):
        """P1: a request without toolbar must still fill the page cache."""
        page = create_page("page", "simple.html", "en")
        url = page.get_absolute_url("en")

        with self.settings(CMS_INTERNAL_IPS=INTERNAL_IPS_ELSEWHERE, MIDDLEWARE=MIDDLEWARE_NO_DJANGO_CACHE):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            # Anonymous, no toolbar, only cacheable content: must be cacheable.
            cache_control = response.headers.get("Cache-Control", "")
            self.assertNotIn("no-cache", cache_control)
            self.assertNotIn("no-store", cache_control)

            with capture_queries() as captured:
                response = self.client.get(url)

            # Served from the page cache: the page is not looked up again.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(queries_on(captured, "cms_pageurl"), [])


class ParentFetchTests(PerfTestCase):
    def test_p8_no_parent_fetch(self):
        """P8: nothing inherits, so the parent page must not be loaded."""
        parent = create_page("parent", "simple.html", "en")
        child = create_page("child", "simple.html", "en", parent=parent)
        add_plugin(child.get_placeholders("en").get(slot="placeholder"), "LinkPlugin", "en", name="a")

        request = self._anon_request(child)
        template = "{% load cms_tags %}{% placeholder 'placeholder' %}"

        with capture_queries() as captured:
            self.render_template_obj(template, {}, request)

        # simple.html declares no inheriting placeholder: no Page query at all.
        self.assertEqual(self._brief(queries_on(captured, "cms_page")), [])


class AncestorLookupTests(PerfTestCase):
    def _is_ancestor_query(self, sql):
        # ``get_ancestor_titles``: page contents filtered by ancestor pages.
        return "cms_pagecontent" in sql and "cms_page" in sql.replace("cms_pagecontent", "") and "path" in sql

    def test_p9_one_ancestor_query(self):
        """P9: template and X-Frame-Options share one ancestor lookup."""
        parent = create_page("parent", "simple.html", "en", xframe_options=constants.X_FRAME_OPTIONS_DENY)
        child = create_page("child", constants.TEMPLATE_INHERITANCE_MAGIC, "en", parent=parent)
        url = child.get_absolute_url("en")

        with self.settings(MIDDLEWARE=MIDDLEWARE_NO_DJANGO_CACHE):
            with capture_queries() as captured:
                response = self.client.get(url)

        # Both values are inherited from the parent ...
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("simple.html", [template.name for template in response.templates])

        # ... and must come from a single query over the ancestors.
        ancestor_queries = [
            query["sql"] for query in captured.captured_queries if self._is_ancestor_query(query["sql"])
        ]
        self.assertLessEqual(len(ancestor_queries), 1, self._brief(ancestor_queries))


class RenderQuerysetTests(PerfTestCase):
    def test_p13_render_queryset_used(self):
        """P13: plugins must be downcast through ``get_render_queryset``."""
        page = create_page("page", "simple.html", "en")
        placeholder = page.get_placeholders("en").get(slot="placeholder")
        add_plugin(placeholder, "LinkPlugin", "en", name="a")
        add_plugin(placeholder, "LinkPlugin", "en", name="b")

        # Stand-in for a plugin that optimises its render queryset
        # (``select_related``, ``prefetch_related``, annotations ...).
        def render_queryset():
            return Link.objects.annotate(perf_marker=Value(1))

        request = self._anon_request(page)

        with mock.patch.object(LinkPlugin, "get_render_queryset", side_effect=render_queryset):
            assign_plugins(request, [placeholder], lang="en")

        plugins = placeholder._plugins_cache
        self.assertEqual(len(plugins), 2)

        for plugin in plugins:
            self.assertEqual(getattr(plugin, "perf_marker", None), 1)


class PageLookupTagTests(PerfTestCase):
    def setUp(self):
        super().setUp()
        self.page = create_page("page", "simple.html", "en")
        self.footer = create_page("footer", "simple.html", "en", reverse_id="footer")
        placeholder = self.footer.get_placeholders("en").get(slot="placeholder")
        add_plugin(placeholder, "LinkPlugin", "en", name="a")

    def _render(self, template):
        # New request per render: only the Django cache carries over.
        request = self._anon_request(self.page)

        with capture_queries() as captured:
            self.render_template_obj("{% load cms_tags %}" + template, {}, request)
        return captured

    def _sql(self, captured):
        return self._brief(query["sql"] for query in captured.captured_queries)

    def test_p14_cached_tag_lookup(self):
        """P14: ``show_placeholder`` with a warm cache needs one lookup query."""
        tag = "{% show_placeholder 'placeholder' 'footer' %}"
        # Fill the placeholder cache.
        self._render(tag)

        captured = self._render(tag)

        # Page, page content and placeholder are resolved by a single query.
        self.assertLessEqual(len(captured), 1, self._sql(captured))

    def test_p14_repeated_tag_memo(self):
        """P14: a repeated ``show_placeholder`` must reuse the first lookup."""
        tag = "{% show_placeholder 'placeholder' 'footer' %}"
        self._render(tag)

        once = self._render(tag)
        twice = self._render(tag + tag)

        # The second tag of a request costs no additional query.
        self.assertEqual(len(twice), len(once), self._sql(twice))

    def test_p15_page_attribute_memo(self):
        """P15: ``page_attribute`` tags with the same lookup share one page."""
        captured = self._render(
            "{% page_attribute 'title' 'footer' %}"
            "{% page_attribute 'page_title' 'footer' %}"
            "{% page_attribute 'menu_title' 'footer' %}"
        )

        # One page lookup and one content lookup for the whole request.
        page_queries = queries_on(captured, "cms_page")
        content_queries = queries_on(captured, "cms_pagecontent")
        self.assertLessEqual(len(page_queries), 1, self._brief(page_queries))
        self.assertLessEqual(len(content_queries), 1, self._brief(content_queries))


class PluginInstantiationTests(PerfTestCase):
    def setUp(self):
        super().setUp()
        # Test-only plugin, not registered by default.
        plugin_pool.register_plugin(NoCachePlugin)
        self.addCleanup(plugin_pool.unregister_plugin, NoCachePlugin)

    def _count_instances(self, request, placeholder):
        """Number of ``NoCachePlugin`` instances built while loading plugins."""
        created = []
        original_init = NoCachePlugin.__init__

        def counting_init(plugin, *args, **kwargs):
            created.append(plugin)
            original_init(plugin, *args, **kwargs)

        with mock.patch.object(NoCachePlugin, "__init__", counting_init):
            assign_plugins(request, [placeholder], lang="en")
        return len(created)

    def _page_with_plugins(self):
        page = create_page("page", "simple.html", "en")
        placeholder = page.get_placeholders("en").get(slot="placeholder")

        for _ in range(3):
            add_plugin(placeholder, "NoCachePlugin", "en")
        return page, placeholder

    def test_p17_one_plugin_instance(self):
        """P17: the cache check must not build a plugin object per plugin."""
        page, placeholder = self._page_with_plugins()

        created = self._count_instances(self._anon_request(page), placeholder)

        # The first uncacheable plugin settles it for the placeholder.
        self.assertFalse(placeholder.cache_placeholder)
        self.assertLessEqual(created, 1)

    def test_p17_skipped_for_staff(self):
        """P17: staff never use the content caches, so nothing is checked."""
        page, placeholder = self._page_with_plugins()

        with self.login_user_context(self.get_superuser()):
            created = self._count_instances(self._anon_request(page), placeholder)

        self.assertEqual(created, 0)


class TemplateConfCacheTests(PerfTestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(self._clear_template_conf_cache)
        self.page = create_page("page", "simple.html", "en")

    def _clear_template_conf_cache(self):
        # Only exists as long as the method is wrapped by ``lru_cache``.
        cache_clear = getattr(CMSPluginBase._get_template_for_conf, "cache_clear", None)

        if cache_clear:
            cache_clear()

    def _content(self):
        return PageContent.objects.get(page=self.page, language="en")

    def _template_for_conf(self, content):
        """The template ``get_require_parent`` passes to the placeholder conf."""
        seen = []

        def fake_conf(setting, placeholder, template=None, default=None):
            seen.append(str(template))
            return default

        with mock.patch("cms.utils.placeholder.get_placeholder_conf", side_effect=fake_conf):
            LinkPlugin.get_require_parent("placeholder", page=content)
        return seen[-1]

    def test_p23_template_not_stale(self):
        """P23: a template change must be visible to the next request."""
        self.assertEqual(self._template_for_conf(self._content()), "simple.html")

        PageContent.objects.filter(page=self.page).update(template="col_two.html")

        # New instance, as loaded by a later request.
        self.assertEqual(self._template_for_conf(self._content()), "col_two.html")

    def test_p23_content_not_pinned(self):
        """P23: restriction lookups must not keep request objects alive."""
        content = self._content()
        reference = weakref.ref(content)
        self._template_for_conf(content)

        del content
        gc.collect()

        self.assertIsNone(reference())


class ProcessorImportTests(PerfTestCase):
    def test_m2_processors_once(self):
        """M2: processors are resolved once per request, not per plugin."""
        page = create_page("page", "simple.html", "en")
        placeholder = page.get_placeholders("en").get(slot="placeholder")

        for name in ("a", "b", "c"):
            add_plugin(placeholder, "LinkPlugin", "en", name=name)

        request = self._anon_request(page)
        template = "{% load cms_tags %}{% placeholder 'placeholder' %}"
        overrides = {
            "CMS_PLUGIN_PROCESSORS": (PLUGIN_PROCESSOR,),
            "CMS_PLUGIN_CONTEXT_PROCESSORS": (CONTEXT_PROCESSOR,),
        }

        with self.settings(**overrides):
            with mock.patch("cms.plugin_rendering.import_string", wraps=import_string) as importer:
                content = self.render_template_obj(template, {}, request)

        # All three plugins were rendered ...
        self.assertEqual(content.count("<a "), 3)

        # ... with one import per processor path.
        imported = [call.args[0] for call in importer.call_args_list]
        self.assertLessEqual(imported.count(PLUGIN_PROCESSOR), 1)
        self.assertLessEqual(imported.count(CONTEXT_PROCESSOR), 1)
