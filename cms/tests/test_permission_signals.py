"""Tests for the permission signal receivers."""
import contextlib
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, update_last_login
from django.db import connection
from django.test.utils import CaptureQueriesContext

from cms.models import PageUser, PageUserGroup
from cms.signals import permissions as permission_signals
from cms.test_utils.testcases import CMSTestCase
from cms.utils.permissions import current_user

User = get_user_model()


@contextlib.contextmanager
def patched_permission_caches():
    """Replace everything the receivers use to invalidate caches."""
    with patch.object(permission_signals, "menu_pool") as menu_pool:
        with patch.object(permission_signals, "clear_user_permission_cache") as clear_cache:
            yield menu_pool, clear_cache


class PermissionCacheAssertionsMixin:
    def assertNoCacheInvalidation(self, menu_pool, clear_cache):
        self.assertFalse(menu_pool.clear.called, "menu_pool.clear() should not have been called")
        self.assertFalse(clear_cache.called, "clear_user_permission_cache() should not have been called")

    def assertCachesClearedFor(self, menu_pool, clear_cache, user):
        menu_pool.clear.assert_called_once_with(all=True)
        clear_cache.assert_called_once_with(user)


class UserSaveSignalTests(PermissionCacheAssertionsMixin, CMSTestCase):
    """Saving users must only invalidate caches when it can matter."""

    def setUp(self):
        super().setUp()
        self.user = self._create_user("login-user", is_staff=True)
        self.creator = self._create_user("creator", is_staff=True, is_superuser=True)

    def test_last_login_update_keeps_caches(self):
        with patched_permission_caches() as mocks:
            update_last_login(None, self.user)
        self.assertNoCacheInvalidation(*mocks)

    def test_other_field_updates_still_clear_caches(self):
        self.user.is_superuser = True
        with patched_permission_caches() as mocks:
            self.user.save(update_fields=["last_login", "is_superuser"])
        self.assertCachesClearedFor(*mocks, self.user)

    def test_created_user_is_not_saved_again(self):
        with current_user(self.creator), CaptureQueriesContext(connection) as queries:
            user = User.objects.create(**{User.USERNAME_FIELD: "created-user"})
        page_user = PageUser.objects.get(pk=user.pk)
        self.assertEqual(page_user.created_by, self.creator)
        user_updates = [
            query["sql"] for query in queries.captured_queries
            if query["sql"].startswith("UPDATE") and User._meta.db_table in query["sql"]
        ]
        self.assertEqual(user_updates, [])

    def test_created_group_is_not_saved_again(self):
        with current_user(self.creator), CaptureQueriesContext(connection) as queries:
            group = Group.objects.create(name="created-group")
        page_group = PageUserGroup.objects.get(pk=group.pk)
        self.assertEqual(page_group.created_by, self.creator)
        group_updates = [
            query["sql"] for query in queries.captured_queries
            if query["sql"].startswith("UPDATE") and Group._meta.db_table in query["sql"]
        ]
        self.assertEqual(group_updates, [])
