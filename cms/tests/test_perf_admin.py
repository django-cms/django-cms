"""
Performance regression tests for edit mode, the structure board and the admin.

Each test targets one finding of the performance audit (ID in the docstring)
and asserts on the specific symptom, not on total query counts.
"""
import re
from contextlib import ExitStack
from unittest import mock

from django.contrib.sites.models import Site
from django.core.cache import cache

from cms.api import add_plugin, create_page
from cms.models import PageContent
from cms.plugin_pool import plugin_pool
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.perf import capture_queries, queries_on
from cms.toolbar.utils import get_object_edit_url, get_object_structure_url
from cms.utils.plugins import get_plugin_restrictions
from cms.utils.urlutils import admin_reverse
from cms.wizards.wizard_base import get_entries

PLUGIN_TABLE = "cms_cmsplugin"
SITE_TABLE = "django_site"
# Full plugin rows select ``plugin_type``; the filled-languages lookup does not.
FULL_PLUGIN_ROW = re.compile(r"plugin_type")


class PerfAdminTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def _create_filled_page(self, template):
        """Page with two plugin models in every placeholder of ``template``."""
        page = create_page(f"perf {template}", template, "en")
        content = self.get_pagecontent_obj(page, "en")

        for placeholder in content.rescan_placeholders().values():
            add_plugin(placeholder, "TextPlugin", "en", body="text")
            add_plugin(placeholder, "LinkPlugin", "en", name="link", external_link="https://example.com")
            # A second language makes the "copy from" lookup return something
            add_plugin(placeholder, "TextPlugin", "de", body="text")
        return content


class StructureBoardPerfTests(PerfAdminTestCase):
    def _structure_plugin_sql(self, content):
        """All SELECTs touching the plugin table while rendering the structure board."""
        url = get_object_structure_url(content, language="en")

        with self.login_user_context(self.get_superuser()):
            with capture_queries() as captured:
                response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        return queries_on(captured, PLUGIN_TABLE)

    def test_e1_structure_bulk_fetch(self):
        """E1: the structure board fetches plugins once, not once per placeholder."""
        two_slots = self._create_filled_page("col_two.html")
        three_slots = self._create_filled_page("col_three.html")

        fetches_two = [sql for sql in self._structure_plugin_sql(two_slots) if FULL_PLUGIN_ROW.search(sql)]
        fetches_three = [sql for sql in self._structure_plugin_sql(three_slots) if FULL_PLUGIN_ROW.search(sql)]

        # One base query plus one downcast query per plugin model,
        # regardless of the number of placeholders.
        self.assertGreater(len(fetches_two), 0)
        self.assertLessEqual(
            len(fetches_three),
            len(fetches_two),
            "Plugin fetch queries grow with the number of placeholders:\n" + "\n".join(fetches_three),
        )

    def test_e7_filled_languages_bulk(self):
        """E7: the dragbar's filled-languages lookup is not one query per placeholder."""
        two_slots = self._create_filled_page("col_two.html")
        three_slots = self._create_filled_page("col_three.html")

        lookups_two = [sql for sql in self._structure_plugin_sql(two_slots) if not FULL_PLUGIN_ROW.search(sql)]
        lookups_three = [sql for sql in self._structure_plugin_sql(three_slots) if not FULL_PLUGIN_ROW.search(sql)]

        self.assertLessEqual(
            len(lookups_three),
            len(lookups_two),
            "Filled-language queries grow with the number of placeholders:\n" + "\n".join(lookups_three),
        )


class PluginRestrictionPerfTests(PerfAdminTestCase):
    def test_e9_restriction_cache_hit(self):
        """E9: a restriction-cache hit does not rescan all registered plugins."""
        page = create_page("perf restrictions", "col_two.html", "en")
        content = self.get_pagecontent_obj(page, "en")
        placeholder = content.rescan_placeholders()["col_left"]
        containers = [add_plugin(placeholder, "MultiColumnPlugin", "en") for _ in range(5)]
        restrictions_cache = {}

        # The first call fills the cache, the second may prime lazily built lookups.
        for plugin in containers[:2]:
            get_plugin_restrictions(plugin, page=content, restrictions_cache=restrictions_cache)

        with mock.patch.object(plugin_pool, "get_all_plugins", wraps=plugin_pool.get_all_plugins) as get_all:
            for plugin in containers[2:]:
                get_plugin_restrictions(plugin, page=content, restrictions_cache=restrictions_cache)

        self.assertEqual(
            get_all.call_count,
            0,
            "get_all_plugins() is called for every container plugin although its restrictions are cached",
        )


class PageTreePerfTests(PerfAdminTestCase):
    def _tree_site_sql(self, branches):
        """Site SELECTs of the page tree endpoint with ``branches`` open branch nodes."""
        endpoint = self.get_admin_url(PageContent, "get_tree")
        data = {"site": 1, "openNodes[]": [page.pk for page in branches]}

        with self.login_user_context(self.get_superuser()):
            with capture_queries() as captured:
                response = self.client.get(endpoint, data=data)

        self.assertEqual(response.status_code, 200)

        for page in branches:
            # Make sure the branch was expanded, i.e. the recursion happened
            self.assertContains(response, f"child of {page.pk}")
        return queries_on(captured, SITE_TABLE)

    def test_e3_tree_site_lookup(self):
        """E3: the page tree resolves the ``site`` parameter once, not per branch node."""
        branches = []

        for index in range(6):
            parent = create_page(f"branch {index}", "nav_playground.html", "en")
            create_page(f"child of {parent.pk}", "nav_playground.html", "en", parent=parent)
            branches.append(parent)

        site_sql_few = self._tree_site_sql(branches[:2])
        site_sql_many = self._tree_site_sql(branches)

        self.assertLessEqual(
            len(site_sql_many),
            len(site_sql_few),
            "Site queries grow with the number of open branch nodes",
        )


class ToolbarPerfTests(PerfAdminTestCase):
    def test_e11_admin_menu_sites(self):
        """E11: with a single site, a staff page view does not load the full site list."""
        self.assertEqual(Site.objects.count(), 1)
        page = create_page("perf toolbar", "nav_playground.html", "en")
        url = get_object_edit_url(self.get_pagecontent_obj(page, "en"))

        with self.login_user_context(self.get_superuser()):
            # Warm up anything a fix may cache per process
            self.client.get(url)

            with capture_queries() as captured:
                response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Unfiltered SELECT of whole rows: only needed to build the multi-site menu
        site_lists = [
            sql for sql in queries_on(captured, SITE_TABLE)
            if "domain" in sql and "WHERE" not in sql.upper()
        ]
        self.assertEqual(site_lists, [])

    def test_e11_wizard_checks_lazy(self):
        """E11: wizard permission checks do not run on every staff page view."""
        page = create_page("perf wizard", "nav_playground.html", "en")
        url = get_object_edit_url(self.get_pagecontent_obj(page, "en"))
        entries = list(get_entries())
        self.assertGreater(len(entries), 1)

        with ExitStack() as stack:
            stack.enter_context(self.login_user_context(self.get_superuser()))
            # Wizards override the check, so every registered entry is patched
            checks = [
                stack.enter_context(mock.patch.object(entry, "user_has_add_permission", return_value=True))
                for entry in entries
            ]
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # One allowed wizard is enough to know the button is enabled
        self.assertLessEqual(sum(check.call_count for check in checks), 1)

    def test_e15_toolbar_init_once(self):
        """E15: ``{% cms_toolbar %}`` does not repeat the toolbar initialisation."""
        page = create_page("perf toolbar init", "nav_playground.html", "en")
        url = get_object_edit_url(self.get_pagecontent_obj(page, "en"))

        with self.login_user_context(self.get_superuser()):
            # ``init_toolbar`` reverses the admin index to detect a missing admin
            with mock.patch("cms.toolbar.toolbar.admin_reverse", wraps=admin_reverse) as reverse_mock:
                response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cms-toolbar")
        index_lookups = [call for call in reverse_mock.call_args_list if call.args == ("index",)]
        self.assertLessEqual(len(index_lookups), 1, "init_toolbar() ran more than once for one request")
