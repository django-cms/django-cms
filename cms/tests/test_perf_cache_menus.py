"""
Performance regression tests for caches, menus and middleware.

Each test pins one finding of the 2026-09 performance audit (the ID is the
first word of the docstring). They assert on the specific symptom -- queries
on one table, cache round trips on one key family, calls of one function --
and never on total counts, so they do not dictate how a fix is implemented.
"""
import re
from collections import Counter
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.urls.resolvers import URLResolver

from cms.api import add_plugin, create_page
from cms.cache.permissions import PERMISSION_KEYS
from cms.cache.placeholder import set_placeholder_cache
from cms.models import PageContent, PagePermission
from cms.plugin_base import CMSPluginBase
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.perf import capture_queries, count_cache_calls, queries_on
from cms.toolbar_base import CMSToolbar as CMSToolbarBase
from cms.utils import apphook_reload
from menus.menu_pool import menu_pool

# Django's own page cache would answer before the CMS page cache is reached.
DJANGO_CACHE_MIDDLEWARE = (
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
)
CMS_ONLY_MIDDLEWARE = [mw for mw in settings.MIDDLEWARE if mw not in DJANGO_CACHE_MIDDLEWARE]

CACHE_READS = ("get", "get_many")
SESSION_KEY_FRAGMENT = "django.contrib.sessions"
IN_LIST_PATTERN = re.compile(r"\bIN\s*\(([^()]*)\)", re.IGNORECASE)


def longest_in_list(sql):
    """
    Number of items of the longest ``IN (...)`` list in ``sql``.

    Example: ``... WHERE id IN (1, 2, 3) AND lang IN ('en')`` returns 3.
    """
    return max((len(items.split(",")) for items in IN_LIST_PATTERN.findall(sql)), default=0)


class PerfTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        menu_pool.clear(all=True)

    def tearDown(self):
        menu_pool.clear(all=True)
        cache.clear()
        super().tearDown()

    def get_menu_nodes(self, user=None, path="/en/"):
        """Build the menu the way a fresh request does."""
        request = self.get_request(path)

        if user:
            request.user = user
        return menu_pool.get_renderer(request).get_nodes()

    def non_session_calls(self, calls, *ops):
        return [call for call in calls.ops(*ops) if SESSION_KEY_FRAGMENT not in str(call[1])]


class MiddlewarePerfTests(PerfTestCase):
    def test_p2_revision_query(self):
        """P2: ApphookReloadMiddleware must not query the revision on every request."""
        previous_revision = apphook_reload.get_local_revision()
        self.addCleanup(apphook_reload.set_local_revision, previous_revision)

        page = create_page("home", "nav_playground.html", "en")
        url = page.get_absolute_url()
        middleware = ["cms.middleware.utils.ApphookReloadMiddleware"] + settings.MIDDLEWARE

        with self.settings(MIDDLEWARE=middleware):
            # First request creates the revision and syncs this process.
            self.client.get(url)

            with capture_queries() as captured:
                response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(queries_on(captured, "cms_urlconfrevision"), [])

    def _hit_page_cache(self):
        """Warm the CMS page cache as anonymous, then return the page url."""
        page = create_page("home", "nav_playground.html", "en")
        url = page.get_absolute_url()
        self.client.get(url)
        return url

    def test_p18_no_toolbars_on_hit(self):
        """P18: An anonymous page cache hit must not instantiate the registered toolbars."""
        created = []
        original_init = CMSToolbarBase.__init__

        def counting_init(instance, *args, **kwargs):
            created.append(type(instance).__name__)
            original_init(instance, *args, **kwargs)

        with self.settings(MIDDLEWARE=CMS_ONLY_MIDDLEWARE):
            url = self._hit_page_cache()

            with mock.patch.object(CMSToolbarBase, "__init__", counting_init):
                with capture_queries() as captured:
                    response = self.client.get(url)

        # Proves the response came from the CMS page cache.
        self.assertEqual(queries_on(captured, "cms_page"), [])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(created, [])

    def test_p18_resolves_on_hit(self):
        """P18: An anonymous page cache hit resolves the url at most once on top of Django."""
        state = {"depth": 0, "calls": 0}
        original_resolve = URLResolver.resolve

        def counting_resolve(resolver, path):
            # Included urlconfs recurse into resolve(), count the entry only.
            if state["depth"] == 0:
                state["calls"] += 1
            state["depth"] += 1

            try:
                return original_resolve(resolver, path)
            finally:
                state["depth"] -= 1

        with self.settings(MIDDLEWARE=CMS_ONLY_MIDDLEWARE):
            url = self._hit_page_cache()

            with mock.patch.object(URLResolver, "resolve", counting_resolve):
                response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # One call belongs to Django's request handler.
        self.assertLessEqual(state["calls"], 2)


class PageCachePerfTests(PerfTestCase):
    def test_p19_cache_hit_reads(self):
        """P19: A page cache hit costs at most two cache round trips."""
        page = create_page("home", "nav_playground.html", "en")
        url = page.get_absolute_url()

        with self.settings(MIDDLEWARE=CMS_ONLY_MIDDLEWARE):
            self.client.get(url)

            with capture_queries() as captured, count_cache_calls() as calls:
                response = self.client.get(url)

        # Proves the response came from the CMS page cache.
        self.assertEqual(queries_on(captured, "cms_page"), [])
        self.assertEqual(response.status_code, 200)

        reads = self.non_session_calls(calls, *CACHE_READS)
        self.assertLessEqual(len(reads), 2, reads)

    def test_p19_page_url_version(self):
        """P19: Several {% page_url %} tags read the page cache version once per request."""
        pages = [create_page(f"page {index}", "nav_playground.html", "en") for index in range(3)]
        template = "{% load cms_tags %}" + "".join(f"{{% page_url {page.pk} %}}" for page in pages)

        # Warm the url cache.
        self.render_template_obj(template, {}, self.get_request("/en/"))

        with count_cache_calls() as calls:
            output = self.render_template_obj(template, {}, self.get_request("/en/"))

        for page in pages:
            self.assertIn(page.get_absolute_url(), output)

        version_reads = calls.keys_containing("_PAGE_CACHE_VERSION", *CACHE_READS)
        self.assertLessEqual(len(version_reads), 1, version_reads)


class PlaceholderCachePerfTests(PerfTestCase):
    slots = ("col_sidebar", "col_left", "col_right")

    def _create_page(self):
        page = create_page("home", "col_three.html", "en")

        for placeholder in page.get_placeholders("en"):
            add_plugin(placeholder, "TextPlugin", "en", body=placeholder.slot)
        return page

    def _placeholder_calls(self, calls, *ops):
        found = calls.keys_containing("placeholder_cache_version", *ops)
        found += calls.keys_containing("render_placeholder", *ops)
        return found

    def test_p16_placeholder_reads(self):
        """P16: Reading N cached placeholders costs fewer than 2N cache round trips."""
        page = self._create_page()
        url = page.get_absolute_url()
        overrides = {"MIDDLEWARE": CMS_ONLY_MIDDLEWARE, "CMS_PAGE_CACHE": False}

        with self.settings(**overrides):
            # Warm the placeholder cache.
            self.client.get(url)

            with capture_queries() as captured, count_cache_calls() as calls:
                response = self.client.get(url)

        for slot in self.slots:
            self.assertContains(response, slot)

        # Proves all placeholders came from the placeholder cache.
        self.assertEqual(queries_on(captured, "cms_cmsplugin"), [])

        reads = self._placeholder_calls(calls, *CACHE_READS)
        self.assertLess(len(reads), 2 * len(self.slots), reads)

    def test_p16b_plugin_walks(self):
        """P16b: Caching a rendered page asks each plugin for its ttl and vary headers once."""
        page = self._create_page()
        url = page.get_absolute_url()
        ttl_calls = Counter()
        vary_calls = Counter()
        original_ttl = CMSPluginBase.get_cache_expiration
        original_vary = CMSPluginBase.get_vary_cache_on

        def counting_ttl(plugin, request, instance, placeholder):
            ttl_calls[instance.pk] += 1
            return original_ttl(plugin, request, instance, placeholder)

        def counting_vary(plugin, request, instance, placeholder):
            vary_calls[instance.pk] += 1
            return original_vary(plugin, request, instance, placeholder)

        with self.settings(MIDDLEWARE=CMS_ONLY_MIDDLEWARE):
            with mock.patch.object(CMSPluginBase, "get_cache_expiration", counting_ttl):
                with mock.patch.object(CMSPluginBase, "get_vary_cache_on", counting_vary):
                    response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Guards the setup: every plugin took part in the cache decision.
        self.assertEqual(len(ttl_calls), len(self.slots))
        self.assertEqual(len(vary_calls), len(self.slots))

        self.assertLessEqual(max(ttl_calls.values()), 1, ttl_calls)
        self.assertLessEqual(max(vary_calls.values()), 1, vary_calls)

    def test_p16b_write_trips(self):
        """P16b: Writing one placeholder to the cache costs at most three cache round trips."""
        page = self._create_page()
        placeholder = page.get_placeholders("en").get(slot="col_left")
        request = self.get_request(page.get_absolute_url())
        content = {"content": "content", "sekizai": {}}

        # The first write creates the version key, measure a regular write.
        set_placeholder_cache(placeholder, "en", 1, content, request)

        with count_cache_calls() as calls:
            set_placeholder_cache(placeholder, "en", 1, content, request)

        trips = self._placeholder_calls(calls)
        self.assertLessEqual(len(trips), 3, trips)


class MenuPerfTests(PerfTestCase):
    def _attach_menus(self):
        """Pages using CMSAttachMenu subclasses, so that ``get_instances`` has work to do."""
        create_page("home", "nav_playground.html", "en")

        for menu in ("StaticMenu", "StaticMenu2"):
            create_page(menu, "nav_playground.html", "en", navigation_extenders=menu)

    def test_p6_attach_instances(self):
        """P6: A warm menu must not query the pages of every CMSAttachMenu again."""
        self._attach_menus()
        warm_nodes = self.get_menu_nodes()
        namespaces = {node.namespace for node in warm_nodes}

        # Guards the setup: the attached menus are part of the tree.
        self.assertTrue(any(namespace.startswith("StaticMenu:") for namespace in namespaces), namespaces)

        with capture_queries() as captured:
            nodes = self.get_menu_nodes()

        self.assertEqual(len(nodes), len(warm_nodes))
        self.assertEqual(queries_on(captured, "cms_page"), [])

    def test_p7_cache_key_lookup(self):
        """P7: A warm menu must not check its cache key in the database."""
        self._attach_menus()
        warm_nodes = self.get_menu_nodes()

        with capture_queries() as captured:
            nodes = self.get_menu_nodes()

        self.assertEqual(len(nodes), len(warm_nodes))
        self.assertEqual(queries_on(captured, "menus_cachekey"), [])

    def _page_queries_for_menu(self, user):
        menu_pool.clear(all=True)

        with capture_queries() as captured:
            self.get_menu_nodes(user=user)
        return queries_on(captured, "cms_page")

    def test_p11_restriction_queries(self):
        """P11: Building the menu must not fetch a page per ``can_view`` restriction."""
        user = self.get_standard_user()
        create_page("home", "nav_playground.html", "en")
        restricted = create_page("restricted", "nav_playground.html", "en")
        groups = [Group.objects.create(name=f"group {index}") for index in range(6)]

        for group in groups[:2]:
            PagePermission.objects.create(page=restricted, group=group, can_view=True)
        few_restrictions = self._page_queries_for_menu(user)

        for group in groups[2:]:
            PagePermission.objects.create(page=restricted, group=group, can_view=True)
        many_restrictions = self._page_queries_for_menu(user)

        # Four more restrictions on the same page must not cost four more page queries.
        self.assertEqual(len(many_restrictions), len(few_restrictions))

    def test_p12_page_url_prefetch(self):
        """P12: The menu's PageUrl prefetch must not list one parameter per page."""
        page_count = 12

        for index in range(page_count):
            create_page(f"page {index}", "nav_playground.html", "en")

        with capture_queries() as captured:
            nodes = self.get_menu_nodes()

        page_nodes = [node for node in nodes if node.attr.get("is_page")]
        self.assertEqual(len(page_nodes), page_count)

        url_queries = queries_on(captured, "cms_pageurl")
        self.assertTrue(url_queries)

        for sql in url_queries:
            self.assertLess(longest_in_list(sql), page_count, sql)


class PermissionCachePerfTests(PerfTestCase):
    def test_e2_tree_perm_reads(self):
        """E2: The page tree reads each cached permission once, not once per row."""
        page_count = 8
        staff = self.get_staff_user_with_std_permissions()
        endpoint = self.get_admin_url(PageContent, "get_tree")

        for index in range(page_count):
            page = create_page(f"page {index}", "nav_playground.html", "en")
            self.add_page_permission(
                staff,
                page,
                can_add=True,
                can_change=True,
                can_delete=True,
                can_publish=True,
                can_move_page=True,
                can_change_advanced_settings=True,
            )

        with self.login_user_context(staff):
            # Warm the permission cache.
            self.client.get(endpoint)

            with count_cache_calls() as calls:
                response = self.client.get(endpoint)

        for index in range(page_count):
            self.assertContains(response, f"page {index}")

        reads = calls.keys_containing(":permission:", *CACHE_READS)
        # Version and value, once per action at most.
        self.assertLessEqual(len(reads), 2 * len(PERMISSION_KEYS), len(reads))
