"""
Performance regression tests for models, permissions, i18n and conf.

Each test is named after its finding in the performance audit
(P = public request path, E = edit mode / admin).
"""
import os
import re
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, update_last_login
from django.core.cache import cache
from django.db import models
from django.test.utils import override_settings

from cms.api import add_plugin, create_page
from cms.forms.utils import get_page_choices_for_site
from cms.models import CMSPlugin, Page, PagePermission, Placeholder
from cms.models.contentmodels import EmptyPageContent
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.perf import capture_queries, queries_on
from cms.utils import get_current_site, i18n
from cms.utils.conf import get_cms_setting
from cms.utils.page_permissions import user_can_delete_page
from menus.menu_pool import menu_pool
from menus.models import CacheKey

TEMPLATE = "nav_playground.html"

# Django prefetches filter on ``<fk> IN (...)``
PREFETCH_PATTERN = re.compile(r'page_id["`]?\s+IN\s*\(', re.IGNORECASE)

# Records one line per execution of the templates dir ``__init__.py`` (P20).
TEMPLATES_INIT = """
import os

with open(os.path.join(os.path.dirname(__file__), "runs.log"), "a") as log:
    log.write("run\\n")

TEMPLATES = {"perf_one.html": "One", "perf_two.html": "Two"}
"""


def selects_from(captured, table):
    """
    SELECT statements whose *primary* table is ``table``.

    ``queries_on`` also matches JOINs and subqueries, which is too broad when
    the unrelated main query legitimately joins the same table.
    """
    pattern = re.compile(rf'^\(?\s*SELECT\s.+?\sFROM\s+["`]?{re.escape(table)}["`]?(\s|$)', re.IGNORECASE | re.DOTALL)
    return [query["sql"] for query in captured.captured_queries if pattern.match(query["sql"])]


def index_field_sets(model):
    """Field name tuples of every index-backed declaration on ``model``."""
    field_sets = [tuple(index.fields) for index in model._meta.indexes]
    field_sets += [tuple(fields) for fields in model._meta.unique_together]
    field_sets += [
        tuple(constraint.fields)
        for constraint in model._meta.constraints
        if isinstance(constraint, models.UniqueConstraint)
    ]
    return field_sets


class PerfTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()


class SignalPerfTests(PerfTestCase):
    def _build_menu_cache(self):
        create_page("home", TEMPLATE, "en")
        request = self.get_request("/en/")
        menu_pool.get_renderer(request).get_nodes()

        # Sanity: the menu cache is registered in the database
        self.assertTrue(CacheKey.objects.exists())

    def test_p3_login_keeps_menu_cache(self):
        """P3: saving only ``last_login`` (every login) must not flush the menu cache."""
        user = self.get_standard_user()
        self._build_menu_cache()

        update_last_login(None, user)

        self.assertTrue(
            CacheKey.objects.exists(),
            "Menu cache was flushed by User.save(update_fields=['last_login'])",
        )

    def test_p3_login_no_site_query(self):
        """P3: a login must not query all sites to clear the user's permission cache."""
        user = self.get_standard_user()

        with capture_queries() as captured:
            update_last_login(None, user)

        self.assertEqual(queries_on(captured, "django_site"), [])

    def test_e10_group_save_site_query(self):
        """E10: saving a group must not query the sites once per group member."""
        group = Group.objects.create(name="editors")

        for name in ("one", "two", "three"):
            user = self._create_user(name, is_staff=True)
            user.groups.add(group)

        with capture_queries() as captured:
            group.save()

        self.assertLessEqual(
            len(queries_on(captured, "django_site")),
            1,
            "Site list is queried for every user of the group",
        )


class IndexPerfTests(PerfTestCase):
    def test_p4_placeholder_gfk_index(self):
        """P4: ``Placeholder.objects.get_for_obj`` needs a (content_type, object_id) index."""
        covered = any(fields[:2] == ("content_type", "object_id") for fields in index_field_sets(Placeholder))

        self.assertTrue(covered, "No index on Placeholder starts with (content_type, object_id)")

    def test_e5_no_duplicate_index(self):
        """E5: CMSPlugin must not declare an index that a unique constraint already creates."""
        unique_sets = [tuple(fields) for fields in CMSPlugin._meta.unique_together]
        unique_sets += [
            tuple(constraint.fields)
            for constraint in CMSPlugin._meta.constraints
            if isinstance(constraint, models.UniqueConstraint)
        ]
        duplicates = [index.fields for index in CMSPlugin._meta.indexes if tuple(index.fields) in unique_sets]

        self.assertEqual(duplicates, [])


class PageUrlPerfTests(PerfTestCase):
    def test_p5_urls_loaded_once(self):
        """P5: asking a page for its URL in every site language hits ``cms_pageurl`` once."""
        page = create_page("page", TEMPLATE, "en")
        page = Page.objects.get(pk=page.pk)
        languages = i18n.get_language_list(site_id=page.site_id)

        with capture_queries() as captured:
            # Same loop as the language chooser (menus/utils.py)
            for language in languages:
                page.get_absolute_url(language, fallback=False)

        self.assertLessEqual(len(selects_from(captured, "cms_pageurl")), 1)

    def test_p5_missing_lang_cached(self):
        """P5: a language without a URL must not re-query on every call."""
        page = create_page("page", TEMPLATE, "en")
        page = Page.objects.get(pk=page.pk)

        with capture_queries() as captured:
            for _ in range(3):
                self.assertIsNone(page.get_path("de", fallback=False))

        self.assertLessEqual(len(selects_from(captured, "cms_pageurl")), 1)

    def test_p5_cache_not_clobbered(self):
        """P5: a URL lookup must not evict already cached languages."""
        page = create_page("page", TEMPLATE, "en")
        url_en = page.urls.get(language="en")
        page.urls.create(language="fr", slug="page-fr", path="page-fr")
        page = Page.objects.get(pk=page.pk)

        with capture_queries() as captured:
            self.assertEqual(page.get_path("en", fallback=False), url_en.path)
            self.assertEqual(page.get_path("fr", fallback=False), "page-fr")
            self.assertEqual(page.get_path("en", fallback=False), url_en.path)

        self.assertLessEqual(len(selects_from(captured, "cms_pageurl")), 1)


class PagePermissionPerfTests(PerfTestCase):
    def test_p10_for_page_no_parent_load(self):
        """P10: ``for_page`` only needs the parent's id, not the parent row."""
        parent = create_page("parent", TEMPLATE, "en")
        child = create_page("child", TEMPLATE, "en", parent=parent)
        child = Page.objects.get(pk=child.pk)

        with capture_queries() as captured:
            list(PagePermission.objects.for_page(child))

        self.assertEqual(selects_from(captured, "cms_page"), [])

    def test_e8_delete_check_batched(self):
        """E8: ``user_can_delete_page`` must not query once per placeholder."""
        page = create_page("page", TEMPLATE, "en")
        placeholders = list(page.get_placeholders("en"))

        # Sanity: the N+1 only shows with several placeholders
        self.assertGreater(len(placeholders), 1)

        for placeholder in placeholders:
            add_plugin(placeholder, "LinkPlugin", "en", name="link", external_link="https://www.django-cms.org")

        user = self.get_staff_user_with_std_permissions()
        self.add_global_permission(user, can_change=True, can_delete=True)
        # Fresh instances: no permission or relation caches
        user = get_user_model().objects.get(pk=user.pk)
        page = Page.objects.get(pk=page.pk)

        with capture_queries() as captured:
            self.assertTrue(user_can_delete_page(user, page))

        self.assertLessEqual(
            len(selects_from(captured, "cms_cmsplugin")),
            1,
            "Plugin types are queried once per placeholder",
        )
        self.assertLessEqual(
            len(selects_from(captured, "cms_pagecontent")),
            1,
            "Placeholder source is fetched once per placeholder",
        )


class ConfPerfTests(PerfTestCase):
    def setUp(self):
        super().setUp()
        self.templates_dir = tempfile.mkdtemp(prefix="cms-perf-templates-")
        self.addCleanup(shutil.rmtree, self.templates_dir, ignore_errors=True)

        with open(os.path.join(self.templates_dir, "__init__.py"), "w") as init_file:
            init_file.write(TEMPLATES_INIT)

    def _get_runs(self):
        log_path = os.path.join(self.templates_dir, "runs.log")

        if not os.path.exists(log_path):
            return 0

        with open(log_path) as log:
            return len(log.readlines())

    def test_p20_templates_dir_memoized(self):
        """P20: the ``CMS_TEMPLATES_DIR`` module must not be re-executed on every settings read."""
        with override_settings(CMS_TEMPLATES_DIR=self.templates_dir):
            first = get_cms_setting("TEMPLATES")
            second = get_cms_setting("TEMPLATES")

        # Sanity: the templates were read from the directory
        self.assertIn("One", [name for _, name in first])
        self.assertEqual(first, second)
        self.assertLessEqual(self._get_runs(), 1)

    def test_p20_empty_content_lazy(self):
        """P20: ``get_admin_content`` must not build an ``EmptyPageContent`` when content exists."""
        page = create_page("page", TEMPLATE, "en")
        page = Page.objects.get(pk=page.pk)
        created = []
        original_init = EmptyPageContent.__init__

        def counting_init(instance, *args, **kwargs):
            created.append(instance)
            original_init(instance, *args, **kwargs)

        with mock.patch.object(EmptyPageContent, "__init__", counting_init):
            content = page.get_admin_content("en")

        self.assertEqual(content.language, "en")
        self.assertEqual(created, [])


class I18nPerfTests(PerfTestCase):
    def test_p21_language_code_once(self):
        """P21: ``get_language_object`` resolves the requested code once, not once per language."""
        site_id = get_current_site().pk
        # Last configured language: the loop has to walk the whole list
        language = i18n.get_language_list(site_id=site_id)[-1]

        with mock.patch("cms.utils.i18n.get_language_code", wraps=i18n.get_language_code) as get_code:
            language_object = i18n.get_language_object(language, site_id=site_id)

        self.assertEqual(language_object["code"], language)
        self.assertLessEqual(get_code.call_count, 1)

    def test_p22_no_fallback_lookup(self):
        """P22: with ``fallback=False`` the fallback languages must not be computed."""
        page = create_page("page", TEMPLATE, "en")
        page = Page.objects.get(pk=page.pk)

        with mock.patch("cms.utils.i18n.get_fallback_languages", wraps=i18n.get_fallback_languages) as get_fallbacks:
            language = page._get_page_content_cache("de", fallback=False, force_reload=False)

        self.assertEqual(language, "de")
        self.assertEqual(get_fallbacks.call_count, 0)

    def test_p22_fallback_lookup_once(self):
        """P22: with ``fallback=True`` the fallback language is computed once."""
        page = create_page("page", TEMPLATE, "en")
        page = Page.objects.get(pk=page.pk)

        with mock.patch("cms.utils.i18n.get_fallback_languages", wraps=i18n.get_fallback_languages) as get_fallbacks:
            language = page._get_page_content_cache("de", fallback=True, force_reload=False)

        # "de" falls back to "fr", then "en"
        self.assertEqual(language, "en")
        self.assertEqual(get_fallbacks.call_count, 1)


class PageChoicesPerfTests(PerfTestCase):
    def test_e6_page_choices_no_n_plus_1(self):
        """E6: building page choices must not load deferred fields page by page."""
        root = create_page("root", TEMPLATE, "en")
        child = create_page("child", TEMPLATE, "en", parent=root)
        create_page("grandchild", TEMPLATE, "en", parent=child)
        site = get_current_site()

        with capture_queries() as captured:
            choices = list(get_page_choices_for_site(site, "en"))

        self.assertEqual(len(choices), 3)
        self.assertLessEqual(len(selects_from(captured, "cms_page")), 1)


class PageCopyPerfTests(PerfTestCase):
    def _copy_tree(self):
        root = create_page("root", TEMPLATE, "en")
        child = create_page("child", TEMPLATE, "en", parent=root)
        grandchild = create_page("grandchild", TEMPLATE, "en", parent=child)
        target = create_page("target", TEMPLATE, "en")
        root = Page.objects.get(pk=root.pk)
        user = self.get_superuser()

        with capture_queries() as captured:
            root.copy_with_descendants(target_page=target, position="last-child", user=user)

        return captured, [child.pk, grandchild.pk]

    def test_e12_contents_read_once(self):
        """E12: descendant contents are either prefetched or read by ``copy()``, not both."""
        captured, descendant_ids = self._copy_tree()
        content_sql = selects_from(captured, "cms_pagecontent")
        prefetched = [sql for sql in content_sql if PREFETCH_PATTERN.search(sql)]
        # copy() reads all contents of its source page: ``WHERE page_id = <pk>``
        reread = [
            sql
            for sql in content_sql
            for pk in descendant_ids
            if re.search(rf'page_id["`]?\s+=\s+{pk}\s*(ORDER BY.*)?$', sql, re.IGNORECASE)
        ]

        self.assertFalse(
            prefetched and reread,
            f"Contents were prefetched and then read again by copy() for {len(reread)} descendant pages",
        )

    def test_e12_no_unused_url_prefetch(self):
        """E12: source page URLs are never read by the copy, so they must not be prefetched."""
        captured, _ = self._copy_tree()
        prefetched = [sql for sql in selects_from(captured, "cms_pageurl") if PREFETCH_PATTERN.search(sql)]

        self.assertEqual(prefetched, [])


class PluginTreePerfTests(PerfTestCase):
    def setUp(self):
        super().setUp()
        page = create_page("page", TEMPLATE, "en")
        placeholder = page.get_placeholders("en").get(slot="body")
        self.root = add_plugin(placeholder, "MultiColumnPlugin", "en")
        self.column = add_plugin(placeholder, "ColumnPlugin", "en", target=self.root)
        self.link = add_plugin(
            placeholder, "LinkPlugin", "en", target=self.column, name="link", external_link="https://www.django-cms.org"
        )

    def test_e13_descendants_one_query(self):
        """E13: fetching a plugin's descendants takes a single query."""
        root = CMSPlugin.objects.get(pk=self.root.pk)

        with capture_queries() as captured:
            descendants = list(root.get_descendants())

        self.assertEqual({plugin.pk for plugin in descendants}, {self.column.pk, self.link.pk})
        self.assertEqual(len(captured), 1)

    def test_e13_ancestors_one_query(self):
        """E13: fetching a plugin's ancestors takes a single query."""
        link = CMSPlugin.objects.get(pk=self.link.pk)

        with capture_queries() as captured:
            ancestors = list(link.get_ancestors_qs())

        self.assertEqual([plugin.pk for plugin in ancestors], [self.root.pk, self.column.pk])
        self.assertEqual(len(captured), 1)
