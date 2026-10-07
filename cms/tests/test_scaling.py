"""
Regression tests for loops whose cost grew quadratically with the number of
menu nodes, plugins or page permissions (#8912).

Each test measures the work done for ``n`` and ``4 * n`` items. Linear work
grows by about 4x, quadratic work by about 16x, so a ratio below
``MAX_GROWTH`` means the code scales linearly.

Work is measured by counting comparisons or hash lookups where possible. Code
whose cost is list copying cannot be counted that way and is timed instead.
"""

import gc
import time
from types import SimpleNamespace
from unittest import mock

from django.contrib.sites.models import Site
from django.db import connection
from django.test.utils import CaptureQueriesContext

from cms.api import create_page
from cms.cms_menus import NavExtender, SoftRootCutter, get_visible_page_contents
from cms.models import ACCESS_PAGE, CMSPlugin, PagePermission
from cms.models.permissionmodels import PermissionTuple
from cms.test_utils.testcases import CMSTestCase
from cms.utils.plugins import downcast_plugins, get_bound_plugins
from menus import utils as menu_utils
from menus.base import NavigationNode
from menus.menu_pool import _build_nodes_inner_for_one_menu
from menus.modifiers import AuthVisibility
from menus.templatetags.menu_tags import cut_levels

# Growth factor between the small and the large input.
SCALE = 4

# Linear code grows by about SCALE, quadratic code by about SCALE ** 2.
MAX_GROWTH = 2 * SCALE

# Timed runs take the fastest of this many repeats to reduce noise.
TIMING_REPEATS = 7


class Work:
    """Counts comparisons and hash lookups made by the code under test."""

    count = 0


class CountingId(int):
    """An integer id that counts how often it is compared or hashed."""

    def __eq__(self, other):
        Work.count += 1
        return int(self) == int(other)

    def __hash__(self):
        Work.count += 1
        return int.__hash__(self)


class CountingName(str):
    """A namespace that counts how often it is compared or hashed."""

    def __eq__(self, other):
        Work.count += 1
        return str(self) == str(other)

    def __hash__(self):
        Work.count += 1
        return str.__hash__(self)


class CountingNode(NavigationNode):
    """A navigation node that counts how often it is compared to another node."""

    def __eq__(self, other):
        Work.count += 1
        return self is other

    __hash__ = NavigationNode.__hash__


class ScalingAssertions:
    def assertLinearCount(self, run, n):
        """``run(size)`` performs the work counted in ``Work.count``."""
        Work.count = 0
        run(n)
        small = Work.count

        Work.count = 0
        run(SCALE * n)
        large = Work.count

        self.assertLess(large, MAX_GROWTH * max(small, 1), f"work grew from {small} to {large}")

    def assertLinearTime(self, setup, n):
        """``setup(size)`` returns a callable that performs the work."""
        small = self._fastest(setup(n))
        large = self._fastest(setup(SCALE * n))
        self.assertLess(large, MAX_GROWTH * small, f"time grew from {small:.6f}s to {large:.6f}s")

    def _fastest(self, work):
        gc.disable()
        try:
            timings = []
            for _ in range(TIMING_REPEATS):
                start = time.perf_counter()
                work()
                timings.append(time.perf_counter() - start)
            return min(timings)
        finally:
            gc.enable()


def make_flat_tree(node_class, size, **attr):
    """
    Return a root node and ``size`` child nodes linked to it.

    ``attr`` is set on the second half of the children only. Tests use it to
    hide those nodes, so each removal has to skip the visible first half.
    """
    root = node_class("root", "/", 0)
    root.namespace = "Menu"
    root.level = 0
    children = []

    for index in range(1, size + 1):
        child = node_class(str(index), f"/{index}/", index, 0, attr=dict(attr) if index > size // 2 else {})
        child.namespace = "Menu"
        child.parent = root
        child.level = 1
        children.append(child)

    root.children = list(children)
    return root, children


class MenuScalingTests(ScalingAssertions, CMSTestCase):
    def test_build_nodes_with_orphans(self):
        """Nodes whose parent is missing (for example an untranslated or restricted parent page)."""

        def run(size):
            nodes = [NavigationNode("root", "/", CountingId(0))]
            nodes += [NavigationNode(str(i), "/", CountingId(i), CountingId(-1)) for i in range(1, size)]
            final_nodes = _build_nodes_inner_for_one_menu(nodes, "Menu")
            self.assertEqual(len(final_nodes), 1)

        self.assertLinearCount(run, 200)

    def test_build_nodes_with_children_first(self):
        """Nodes listed before their parent, as menus not ordered by tree path may return them."""

        def run(size):
            nodes = [NavigationNode(str(i), "/", CountingId(i), CountingId(i - 1) if i else None) for i in range(size)]
            final_nodes = _build_nodes_inner_for_one_menu(nodes[::-1], "Menu")
            self.assertEqual(len(final_nodes), size)

        self.assertLinearCount(run, 100)

    def test_get_descendants(self):
        def setup(size):
            root, children = make_flat_tree(NavigationNode, size)
            return root.get_descendants

        self.assertLinearTime(setup, 2000)

    def test_utils_cut_levels(self):
        def setup(size):
            roots = []
            for index in range(size):
                root, children = make_flat_tree(NavigationNode, 1)
                roots.append(root)
            return lambda: menu_utils.cut_levels(roots, 1)

        self.assertLinearTime(setup, 2000)

    def test_auth_visibility(self):
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))

        def run(size):
            root, children = make_flat_tree(CountingNode, size, visible_for_anonymous=False)
            AuthVisibility(None).modify(request, [root, *children], None, None, False, False)
            self.assertEqual(root.children, children[: size // 2])

        self.assertLinearCount(run, 200)

    def test_menu_tags_cut_levels(self):
        def run(size):
            root, children = make_flat_tree(CountingNode, size)
            root.selected = True
            for child in children[size // 2 :]:
                child.visible = False
            cut_levels([root, *children], 0, 100, 100, 100)
            self.assertEqual(root.children, children[: size // 2])

        self.assertLinearCount(run, 200)

    def test_nav_extender_removes_unattached_nodes(self):
        renderer = SimpleNamespace(menus={"Extender": SimpleNamespace(cms_enabled=True)})
        request = SimpleNamespace(path_info="/")

        def run(size):
            pages = [CountingNode(str(i), "/", i) for i in range(size)]
            extensions = [CountingNode(str(i), "/", -i) for i in range(1, size + 1)]
            for node in pages:
                node.namespace = "CMSMenu"
            for node in extensions:
                node.namespace = "Extender"
            nodes = NavExtender(renderer).modify(request, pages + extensions, None, None, False, False)
            self.assertEqual(nodes, pages)

        self.assertLinearCount(run, 200)

    def test_nav_extender_attaches_nodes(self):
        renderer = SimpleNamespace(menus={})
        request = SimpleNamespace(path_info="/")

        def run(size):
            extension = NavigationNode("ext", "/ext/", "ext")
            extension.namespace = CountingName("Extender")
            pages = [
                NavigationNode(str(i), "/", i, attr={"navigation_extenders": [CountingName("Extender")]})
                for i in range(1, size + 1)
            ]
            for node in pages:
                node.namespace = CountingName("CMSMenu")
            NavExtender(renderer).modify(request, [*pages, extension], None, None, False, False)
            self.assertIs(extension.parent, pages[0])

        self.assertLinearCount(run, 200)

    def test_soft_root_cutter_remove_children(self):
        def run(size):
            others = [CountingNode(str(i), "/", -i) for i in range(1, size + 1)]
            root, children = make_flat_tree(CountingNode, size)
            nodes = [*others, root, *children]
            SoftRootCutter(None).remove_children(root, nodes)
            self.assertEqual(nodes, [*others, root])

        self.assertLinearCount(run, 200)


class PluginScalingTests(ScalingAssertions, CMSTestCase):
    def _make_plugin_chain(self, size):
        """Unsaved plugins without a custom model, each nested in the previous one."""
        return [
            CMSPlugin(pk=index, parent_id=CountingId(index - 1) if index > 1 else None, plugin_type="EmptyPlugin")
            for index in range(1, size + 1)
        ]

    def test_downcast_plugins(self):
        def run(size):
            plugins = self._make_plugin_chain(size)
            self.assertEqual(len(list(downcast_plugins(plugins))), size)

        self.assertLinearCount(run, 200)

    def test_get_bound_plugins(self):
        def run(size):
            plugins = self._make_plugin_chain(size)
            self.assertEqual(len(list(get_bound_plugins(plugins))), size)

        self.assertLinearCount(run, 200)


class ViewRestrictionScalingTests(CMSTestCase):
    template = "nav_playground.html"

    def setUp(self):
        super().setUp()
        self.site = Site.objects.get_current()
        self.user = self.get_standard_user()
        self.pages = [create_page(f"page-{index}", self.template, "en") for index in range(8)]

        # Restrict the later pages: unrestricted pages are checked first.
        for page in self.pages[4:]:
            PagePermission.objects.create(page=page, user=self.user, can_view=True, grant_on=ACCESS_PAGE)

    def _get_page_contents(self):
        return [page.get_content_obj() for page in self.pages]

    def _get_request(self):
        return SimpleNamespace(user=self.user)

    def test_pages_are_only_checked_against_their_restrictions(self):
        """Root pages without ancestors must not be checked against every restriction on the site."""
        page_contents = self._get_page_contents()
        get_visible_page_contents(self._get_request(), page_contents, self.site)  # Warm up permission caches

        with mock.patch.object(
            PermissionTuple, "contains", autospec=True, side_effect=PermissionTuple.contains
        ) as contains:
            visible = get_visible_page_contents(self._get_request(), page_contents, self.site)

        self.assertEqual(visible, page_contents)
        self.assertLessEqual(contains.call_count, len(page_contents))

    def _count_queries(self, page_contents):
        get_visible_page_contents(self._get_request(), page_contents, self.site)  # Warm up permission caches
        with CaptureQueriesContext(connection) as queries:
            get_visible_page_contents(self._get_request(), page_contents, self.site)
        return len(queries.captured_queries)

    def test_number_of_queries_does_not_scale_with_restrictions(self):
        page_contents = self._get_page_contents()
        query_count = self._count_queries(page_contents)

        for page in self.pages[1:4]:
            PagePermission.objects.create(page=page, user=self.user, can_view=True, grant_on=ACCESS_PAGE)

        self.assertEqual(self._count_queries(page_contents), query_count)
