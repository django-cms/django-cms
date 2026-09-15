import warnings
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import OperationalError, ProgrammingError
from django.test.utils import override_settings

from cms.admin.permissionadmin import GlobalPagePermissionAdmin, PagePermissionInlineAdmin
from cms.api import add_plugin, assign_user_to_page, create_page
from cms.cache.permissions import (
    clear_user_permission_cache,
    get_cache_key,
    get_permission_cache,
    set_permission_cache,
)
from cms.models import Page, PageContent
from cms.models.permissionmodels import (
    ACCESS_CHILDREN,
    ACCESS_DESCENDANTS,
    ACCESS_PAGE,
    ACCESS_PAGE_AND_CHILDREN,
    ACCESS_PAGE_AND_DESCENDANTS,
    GlobalPagePermission,
    PagePermission,
    PermissionTuple,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from cms.utils.page_permissions import (
    get_change_perm_tuples,
    has_generic_permission,
    user_can_change_at_least_one_page,
    user_can_delete_page,
    user_can_publish_page,
)


@override_settings(
    CMS_PERMISSION=True,
    CMS_CACHE_DURATIONS={
        'menus': 60,
        'content': 60,
        'permissions': 60,
    },
)
class PermissionCacheTests(CMSTestCase):

    def setUp(self):
        self.user_super = self._create_user("super", is_staff=True,
                                            is_superuser=True)
        self.user_normal = self._create_user("randomuser", is_staff=True,
                                             add_default_permissions=True)
        self.home_page = create_page("home", "nav_playground.html", "en",
                                     created_by=self.user_super)

    def test_basic_permissions(self):
        """
        Test basic permissions cache get / set / clear low-level api
        """
        cached_permissions = get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page")
        self.assertIsNone(cached_permissions)

        set_permission_cache(self.user_normal, Site.objects.get_current(), "change_page", [self.home_page.id])
        cached_permissions = get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page")
        self.assertEqual(cached_permissions, [self.home_page.id])

        clear_user_permission_cache(self.user_normal)
        cached_permissions = get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page")
        self.assertIsNone(cached_permissions)

    def test_permission_manager(self):
        """
        Test page permission manager working on a subpage
        """
        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)
        cached_permissions = get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page")
        self.assertIsNone(cached_permissions)

        live_permissions = get_change_perm_tuples(self.user_normal, Site.objects.get_current())
        cached_permissions_permissions = get_permission_cache(
            self.user_normal, Site.objects.get_current(), "change_page"
        )
        self.assertEqual(live_permissions, [(ACCESS_PAGE_AND_DESCENDANTS, page_b.node.path)])
        self.assertEqual(cached_permissions_permissions, live_permissions)

    def test_cached_permission_precedence(self):
        # refs - https://github.com/divio/django-cms/issues/6335
        # cached page permissions should not override global permissions
        page = create_page(
            "test page",
            "nav_playground.html",
            "en",
            created_by=self.user_super,
        )
        page_permission = GlobalPagePermission.objects.create(
            can_change=True,
            can_publish=True,
            user=self.user_normal,
        )
        page_permission.sites.add(Site.objects.get_current())
        set_permission_cache(self.user_normal, Site.objects.get_current(), "publish_page", [])

        can_publish = user_can_publish_page(
            self.user_normal,
            page,
            Site.objects.get_current(),
        )
        self.assertTrue(can_publish)

    def test_has_generic_permissions_compatibiltiy(self):
        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)

        self.assertTrue(has_generic_permission(page_b, self.user_normal, "change_page"))
        self.assertFalse(has_generic_permission(page_b, self.user_normal, "publish_page"))


@override_settings(CMS_PERMISSION=True, CMS_RAW_ID_USERS=1)
class PermissionAdminMigrationSafetyTests(CMSTestCase):
    """
    Regression tests for the case where the user table does not yet exist
    (e.g. during ``migrate`` on a fresh install with a custom user model).

    Counting users then raises ``OperationalError`` on sqlite or
    ``ProgrammingError`` on postgres. Both must be swallowed so that the
    admin classes can still be imported and registered during migrations.
    """

    def _patched_user_model(self, exc):
        class _BrokenManager:
            def count(self):
                raise exc

        class _BrokenUserModel:
            objects = _BrokenManager()

        return patch(
            'cms.admin.permissionadmin.get_user_model',
            return_value=_BrokenUserModel,
        )

    def test_inline_raw_id_fields_swallows_db_errors(self):
        for exc in (OperationalError("no such table"), ProgrammingError("relation does not exist")):
            with self.subTest(exc=type(exc).__name__), self._patched_user_model(exc):
                self.assertEqual(PagePermissionInlineAdmin.raw_id_fields, [])

    def test_global_admin_raw_id_fields_swallows_db_errors(self):
        for exc in (OperationalError("no such table"), ProgrammingError("relation does not exist")):
            with self.subTest(exc=type(exc).__name__), self._patched_user_model(exc):
                self.assertEqual(GlobalPagePermissionAdmin.raw_id_fields, [])

    def test_global_admin_get_list_filter_swallows_db_errors(self):
        admin_instance = GlobalPagePermissionAdmin(GlobalPagePermission, admin_site=None)
        for exc in (OperationalError("no such table"), ProgrammingError("relation does not exist")):
            with self.subTest(exc=type(exc).__name__), self._patched_user_model(exc):
                # Falls back to the unfiltered list_filter (still includes 'user')
                self.assertIn('user', admin_instance.get_list_filter(request=None))


class PermissionTupleTests(CMSTestCase):
    """
    Regression tests for ``PermissionTuple.allow_list()`` building invalid
    lookups (``page____path__length``) for ACCESS_CHILDREN,
    ACCESS_DESCENDANTS and ACCESS_PAGE_AND_CHILDREN (#8661).
    """

    def setUp(self):
        self.root = create_page("root", "nav_playground.html", "en")
        self.child = create_page("child", "nav_playground.html", "en", parent=self.root)
        self.grandchild = create_page("grandchild", "nav_playground.html", "en", parent=self.child)
        self.sibling = create_page("sibling", "nav_playground.html", "en")

    def test_allow_list_scopes(self):
        cases = (
            (ACCESS_PAGE, {self.root}),
            (ACCESS_CHILDREN, {self.child}),
            (ACCESS_PAGE_AND_CHILDREN, {self.root, self.child}),
            (ACCESS_DESCENDANTS, {self.child, self.grandchild}),
            (ACCESS_PAGE_AND_DESCENDANTS, {self.root, self.child, self.grandchild}),
        )
        for grant_on, expected in cases:
            with self.subTest(grant_on=grant_on):
                perm = PermissionTuple((grant_on, self.root.path))
                allowed = Page.objects.filter(perm.allow_list())
                self.assertEqual(set(allowed), expected)

    def test_allow_list_matches_contains(self):
        pages = list(Page.objects.all())
        grants = (ACCESS_PAGE, ACCESS_CHILDREN, ACCESS_PAGE_AND_CHILDREN,
                  ACCESS_DESCENDANTS, ACCESS_PAGE_AND_DESCENDANTS)
        for grant_on in grants:
            with self.subTest(grant_on=grant_on):
                perm = PermissionTuple((grant_on, self.root.path))
                expected = {page.pk for page in pages if perm.contains(page.path)}
                allowed = Page.objects.filter(perm.allow_list()).values_list("pk", flat=True)
                self.assertEqual(set(allowed), expected)

    def test_allow_list_with_related_field_prefix(self):
        user = self._create_user("perm-user", is_staff=True)
        for page in (self.root, self.child, self.grandchild, self.sibling):
            PagePermission.objects.create(page=page, user=user, grant_on=ACCESS_PAGE)
        perm = PermissionTuple((ACCESS_PAGE_AND_CHILDREN, self.root.path))
        matched = PagePermission.objects.filter(perm.allow_list("page"))
        self.assertEqual({pp.page_id for pp in matched}, {self.root.pk, self.child.pk})
@override_settings(CMS_PERMISSION=True)


class DeletePagePlaceholderPermissionTests(CMSTestCase):
    """
    ``user_can_delete_page`` must evaluate the delete permission of the
    plugins in each of the page's placeholders.

    Regression tests for issue 03: the placeholder loop accessed ``.source``
    on the queryset instead of the loop variable (``AttributeError``), and
    the placeholder lookup filtered on the ``Placeholder`` content type
    instead of ``PageContent``, so the loop never ran at all.
    """

    def _get_page_with_plugin(self):
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot="body")
        add_plugin(
            placeholder,
            "LinkPlugin",
            "en",
            name="A link",
            external_link="https://www.django-cms.org",
        )
        return page

    def test_user_with_plugin_permissions_can_delete_page(self):
        page = self._get_page_with_plugin()
        # add_default_permissions grants add/change/delete on the Link plugin model
        user = self._create_user(
            "page-deleter",
            is_staff=True,
            add_default_permissions=True,
            permissions=["change_page", "delete_page"],
        )
        self.add_global_permission(user, can_change=True, can_delete=True)

        self.assertTrue(user_can_delete_page(user, page))

    def test_user_without_plugin_permissions_cannot_delete_page(self):
        page = self._get_page_with_plugin()
        # No plugin model permissions: deleting the page would delete the
        # Link plugin in its placeholder, which this user may not do.
        user = self._create_user(
            "page-deleter-no-plugin-perms",
            is_staff=True,
            permissions=["change_page", "delete_page"],
        )
        self.add_global_permission(user, can_change=True, can_delete=True)

        self.assertFalse(user_can_delete_page(user, page))


@override_settings(
    CMS_PERMISSION=True,
    CMS_CACHE_DURATIONS={
        'menus': 60,
        'content': 60,
        'permissions': 60,
    },
)
class PermissionCacheInvalidationTests(CMSTestCase):
    """
    Saving or deleting users and changing their group memberships must
    invalidate the permission cache.

    Regression tests for issue 10: the signal handlers were connected to the
    hardcoded ``django.contrib.auth.models.User``, so projects with a custom
    ``AUTH_USER_MODEL`` got no cache invalidation. These tests exercise the
    handlers through the model returned by ``get_user_model()`` and fail in
    test runs with a custom user model (``--auth-user-model``) if the
    binding regresses.
    """

    def setUp(self):
        self.user_super = self._create_user("super", is_staff=True, is_superuser=True)
        self.user_normal = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        self.home_page = create_page("home", "nav_playground.html", "en", created_by=self.user_super)

    def _fill_permission_cache(self):
        set_permission_cache(self.user_normal, Site.objects.get_current(), "change_page", [self.home_page.id])
        self.assertIsNotNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_user_save_clears_permission_cache(self):
        self._fill_permission_cache()
        self.user_normal.save()
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_user_delete_clears_permission_cache(self):
        self._fill_permission_cache()
        self.user_normal.delete()
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_group_membership_change_clears_permission_cache(self):
        group = Group.objects.create(name="permission-cache-group")
        self._fill_permission_cache()
        self.user_normal.groups.add(group)
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_group_delete_clears_permission_cache_of_members(self):
        group = Group.objects.create(name="permission-cache-group")
        self.user_normal.groups.add(group)
        self._fill_permission_cache()
        group.delete()
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))


@override_settings(
    CMS_PERMISSION=True,
    CMS_CACHE_DURATIONS={
        'menus': 60,
        'content': 60,
        'permissions': 60,
    },
    CMS_LANGUAGES={
        1: [{'code': 'en', 'name': 'English'}],
        2: [{'code': 'en', 'name': 'English'}],
    },
)
class PermissionCacheSiteIsolationTests(CMSTestCase):
    """The cached page permissions of one site must not be served for another.

    ``get_page_actions_for_user`` filters by site, so a value warmed while
    browsing a site the user works on used to satisfy the "can change at least
    one page" gate of every other site, disclosing their page trees.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        self.site_a = Site.objects.get_current()
        self.site_b = Site.objects.create(domain='b.example', name='B')
        self.user = self._create_user('editor', is_staff=True, add_default_permissions=True)
        self.page_a = create_page('site-a', 'nav_playground.html', 'en', site=self.site_a)
        assign_user_to_page(self.page_a, self.user, can_view=True, can_change=True)
        self.secret_b = create_page('SECRET-SITE-B', 'nav_playground.html', 'en', site=self.site_b)

    def get_tree(self, site):
        return self.client.get(self.get_admin_url(PageContent, 'get_tree') + f'?site={site.pk}')

    def test_cache_key_includes_the_site(self):
        self.assertNotEqual(
            get_cache_key(self.user, self.site_a, 'change_page'),
            get_cache_key(self.user, self.site_b, 'change_page'),
        )

    def test_cached_permissions_are_not_reused_across_sites(self):
        self.assertTrue(user_can_change_at_least_one_page(self.user, self.site_a))
        self.assertIsNotNone(get_permission_cache(self.user, self.site_a, 'change_page'))
        self.assertIsNone(get_permission_cache(self.user, self.site_b, 'change_page'))
        self.assertFalse(user_can_change_at_least_one_page(self.user, self.site_b))

    def test_warming_one_site_does_not_disclose_another(self):
        with self.login_user_context(self.user):
            self.assertEqual(self.get_tree(self.site_a).status_code, 200)
            # The gate of site B must not be satisfied by the value just warmed.
            response = self.get_tree(self.site_b)
        self.assertEqual(response.status_code, 403)

    def test_own_site_stays_reachable_when_cache_is_warm(self):
        with self.login_user_context(self.user):
            self.get_tree(self.site_b)
            response = self.get_tree(self.site_a)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'site-a')

    def test_clear_user_permission_cache_clears_every_site(self):
        set_permission_cache(self.user, self.site_a, 'change_page', [self.page_a.path])
        set_permission_cache(self.user, self.site_b, 'change_page', [self.secret_b.path])

        clear_user_permission_cache(self.user)

        self.assertIsNone(get_permission_cache(self.user, self.site_a, 'change_page'))
        self.assertIsNone(get_permission_cache(self.user, self.site_b, 'change_page'))


@override_settings(CMS_PERMISSION=True)
class DeprecatedSiteAccessHelperTests(CMSTestCase):
    """``user_can_access_site``/``raise_site_permission_denied`` are unused.

    Site isolation is enforced by ``PageContentAdmin.has_change_permission()``.
    """

    def get_admin(self):
        return admin.site._registry[PageContent]

    def test_user_can_access_site_warns(self):
        request = self.get_request("/en/")
        request.user = self.get_superuser()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RemovedInDjangoCMS60Warning)
            self.assertTrue(self.get_admin().user_can_access_site(request))

        self.assertTrue(
            any(issubclass(warning.category, RemovedInDjangoCMS60Warning) for warning in caught),
            "Expected a deprecation warning from user_can_access_site().",
        )

    def test_raise_site_permission_denied_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RemovedInDjangoCMS60Warning)
            with self.assertRaises(PermissionDenied):
                self.get_admin().raise_site_permission_denied()

        self.assertTrue(
            any(issubclass(warning.category, RemovedInDjangoCMS60Warning) for warning in caught),
            "Expected a deprecation warning from raise_site_permission_denied().",
        )
