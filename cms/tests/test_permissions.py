from django.contrib.sites.models import Site
from django.test.utils import override_settings

from cms.api import create_page, assign_user_to_page
from cms.cache.permissions import (get_permission_cache, set_permission_cache,
                                   clear_user_permission_cache)
from cms.models.permissionmodels import GlobalPagePermission
from cms.test_utils.testcases import CMSTestCase
from cms.utils.page_permissions import get_change_id_list, user_can_publish_page


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
        cached_permissions = get_permission_cache(self.user_normal, "1:change_page")
        self.assertIsNone(cached_permissions)

        set_permission_cache(self.user_normal, "1:change_page", [self.home_page.id])
        cached_permissions = get_permission_cache(self.user_normal, "1:change_page")
        self.assertEqual(cached_permissions, [self.home_page.id])

        clear_user_permission_cache(self.user_normal)
        cached_permissions = get_permission_cache(self.user_normal, "1:change_page")
        self.assertIsNone(cached_permissions)

    def test_permission_manager(self):
        """
        Test page permission manager working on a subpage
        """
        site = Site.objects.get_current()
        cache_key = "%s:%s" % (site.id, "change_page")

        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)
        cached_permissions = get_permission_cache(self.user_normal, cache_key)
        self.assertIsNone(cached_permissions)

        live_permissions = get_change_id_list(self.user_normal, Site.objects.get_current())
        cached_permissions_permissions = get_permission_cache(self.user_normal,
                                                              cache_key)
        self.assertEqual(live_permissions, [page_b.id])
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
        site = Site.objects.get_current()
        page_permission.sites.add(site)
        set_permission_cache(self.user_normal, "%s:publish_page" % site.id, [])

        can_publish = user_can_publish_page(
            self.user_normal,
            page,
            site
        )
        self.assertTrue(can_publish)
