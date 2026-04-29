from unittest.mock import patch

from django.contrib.sites.models import Site
from django.db import OperationalError, ProgrammingError
from django.test.utils import override_settings

from cms.admin.permissionadmin import GlobalPagePermissionAdmin, PagePermissionInlineAdmin
from cms.api import assign_user_to_page, create_page
from cms.cache.permissions import (
    clear_user_permission_cache,
    get_permission_cache,
    set_permission_cache,
)
from cms.models.permissionmodels import ACCESS_PAGE_AND_DESCENDANTS, GlobalPagePermission
from cms.test_utils.testcases import CMSTestCase
from cms.utils.page_permissions import (
    get_change_perm_tuples,
    has_generic_permission,
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
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)

        set_permission_cache(self.user_normal, "change_page", [self.home_page.id])
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertEqual(cached_permissions, [self.home_page.id])

        clear_user_permission_cache(self.user_normal)
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)

    def test_permission_manager(self):
        """
        Test page permission manager working on a subpage
        """
        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)

        live_permissions = get_change_perm_tuples(self.user_normal, Site.objects.get_current())
        cached_permissions_permissions = get_permission_cache(self.user_normal,
                                                              "change_page")
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
        set_permission_cache(self.user_normal, "publish_page", [])

        can_publish = user_can_publish_page(
            self.user_normal,
            page,
            Site.objects.get_current(),
        )
        self.assertTrue(can_publish)

    def test_has_generic_permissions_compatibiltiy(self):
        from cms.utils.permissions import has_page_permission

        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)

        self.assertTrue(has_generic_permission(page_b, self.user_normal, "change_page"))
        self.assertFalse(has_generic_permission(page_b, self.user_normal, "publish_page"))

        # Backwards compatibility: check if the old permission names work
        self.assertTrue(has_page_permission(self.user_normal, page_b, "change"))
        self.assertFalse(has_page_permission(self.user_normal, page_b, "publish"))

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
