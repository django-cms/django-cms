from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from cms.api import assign_user_to_page, create_page
from cms.cache.permissions import (
    clear_user_permission_cache, get_permission_cache, set_permission_cache,
)
from cms.models import Page
from cms.models.permissionmodels import (
    ACCESS_PAGE_AND_DESCENDANTS, GlobalPagePermission,
)
from cms.test_utils.testcases import URL_CMS_PAGE_ADD, CMSTestCase
from cms.utils.page_permissions import (
    get_change_id_list, user_can_add_subpage, user_can_publish_page,
    user_can_view_page,
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

        live_permissions = get_change_id_list(self.user_normal, Site.objects.get_current())
        cached_permissions_permissions = get_permission_cache(self.user_normal,
                                                              "change_page")
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
        page_permission.sites.add(Site.objects.get_current())
        set_permission_cache(self.user_normal, "publish_page", [])

        can_publish = user_can_publish_page(
            self.user_normal,
            page,
            Site.objects.get_current(),
        )
        self.assertTrue(can_publish)

    def test_visibility_after_move_page(self):
        superuser = self.get_superuser()
        user1 = self._create_user("user1", is_staff=True, is_superuser=False)

        visible = create_page("visible", "nav_playground.html", "en", published=True)
        visible_child = create_page("visible_child", "nav_playground.html", "en", parent=visible, published=True)
        invisible_for_user1 = create_page("invisible", "nav_playground.html", "en", published=True)

        assign_user_to_page(visible, user1, grant_on=ACCESS_PAGE_AND_DESCENDANTS, can_view=True)
        assign_user_to_page(invisible_for_user1, superuser, grant_on=ACCESS_PAGE_AND_DESCENDANTS, can_view=True)

        with self.login_user_context(user1):
            response = self.client.get(visible_child.get_public_object().get_absolute_url())
            self.assertEqual(response.status_code, 200)

            response = self.client.get(invisible_for_user1.get_public_object().get_absolute_url())
            self.assertEqual(response.status_code, 404)

        with self.login_user_context(superuser):
            move_url = self.get_admin_url(Page, 'move_page', visible_child.pk)
            response = self.client.post(move_url, {
                'id': visible_child.pk,
                'position': 0,
                'target': invisible_for_user1.pk,
            })
            self.assertEqual(response.status_code, 200)
            visible_child = visible_child.reload()
            self.assertEqual(visible_child.parent_page.pk, invisible_for_user1.pk)

        # Ignore cached_func
        User = get_user_model()
        user1 = User.objects.get(pk=user1.pk)
        self.assertFalse(user_can_view_page(user=user1, page=visible_child))

    def test_add_page_twice(self):
        user1 = self._create_user("user1", is_staff=True, is_superuser=False, add_default_permissions=True)

        home = create_page("home", "nav_playground.html", "en", published=True)
        home.set_as_homepage()
        assign_user_to_page(home, user1, grant_on=ACCESS_PAGE_AND_DESCENDANTS, can_add=True, can_change=True, can_publish=True)

        with self.login_user_context(user1):
            response = self.client.post(f'{URL_CMS_PAGE_ADD}?parent_node={home.node.pk}', self.get_new_page_data(parent_id=home.node.pk))
            self.assertEqual(response.status_code, 302)

        child = home.reload().get_child_pages().first()
        self.assertIsNotNone(child)

        # Ignore cached_func
        User = get_user_model()
        user1 = User.objects.get(pk=user1.pk)
        self.assertTrue(user_can_add_subpage(user1, child))
