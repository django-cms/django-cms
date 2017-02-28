# -*- coding: utf-8 -*-
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from cms.api import create_page, assign_user_to_page
from cms.cache.permissions import (get_permission_cache, set_permission_cache,
                                   clear_user_permission_cache)
from cms.test_utils.testcases import CMSTestCase
from cms.utils.page_permissions import get_change_id_list


@override_settings(CMS_PERMISSION=True)
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

    def test_cache_invalidation(self):
        """
        Test permission cache clearing on page save
        """
        set_permission_cache(self.user_normal, "change_page", [self.home_page.id])

        self.home_page.save()
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

        live_permissions = get_change_id_list(self.user_normal, Site.objects.get_current())
        cached_permissions_permissions = get_permission_cache(self.user_normal,
                                                              "change_page")
        self.assertEqual(live_permissions, [page_b.id])
        self.assertEqual(cached_permissions_permissions, live_permissions)

        self.home_page.save()
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)
