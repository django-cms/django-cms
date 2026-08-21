"""Tests for the permission signal receivers and their handling of ``raw`` events.

``loaddata`` saves objects with ``raw=True`` and, as of Django 6.1, also forwards
``raw=True`` to ``m2m_changed``. While a fixture is being loaded the related rows
are not guaranteed to exist yet, so the receivers must not hit the database or
invalidate any cache.
"""
import contextlib
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS

from cms.models import GlobalPagePermission, PagePermission
from cms.signals import permissions as permission_signals
from cms.test_utils.testcases import CMSTestCase

User = get_user_model()

#: Only Django 6.1+ tells receivers that an ``m2m_changed`` event belongs to a fixture.
M2M_CHANGED_SENDS_RAW = django.VERSION >= (6, 1)


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


class UserGroupsRawSignalTests(PermissionCacheAssertionsMixin, CMSTestCase):
    """``m2m_changed`` on ``User.groups`` must ignore fixture loading events."""

    def setUp(self):
        super().setUp()
        self.user = self._create_user("m2m-user", is_staff=True)
        self.group = Group.objects.create(name="m2m-group")

    def send(self, action, reverse=False, **kwargs):
        """Mimic what Django sends for ``User.groups.through``."""
        permission_signals.user_m2m_changed(
            instance=self.group if reverse else self.user,
            action=action,
            reverse=reverse,
            model=User if reverse else Group,
            pk_set={self.user.pk if reverse else self.group.pk},
            using=DEFAULT_DB_ALIAS,
            **kwargs,
        )

    def test_raw_forward_event_is_ignored(self):
        with patched_permission_caches() as mocks:
            with self.assertNumQueries(0):
                self.send("pre_add", raw=True)
        self.assertNoCacheInvalidation(*mocks)

    def test_raw_reverse_event_is_ignored(self):
        # Without the guard this would query the users referenced by ``pk_set``.
        with patched_permission_caches() as mocks:
            with self.assertNumQueries(0):
                self.send("pre_remove", reverse=True, raw=True)
        self.assertNoCacheInvalidation(*mocks)

    def test_regular_forward_event_clears_caches(self):
        for action in ("pre_add", "pre_remove"):
            with self.subTest(action=action):
                with patched_permission_caches() as mocks:
                    self.send(action, raw=False)
                self.assertCachesClearedFor(*mocks, self.user)

    def test_regular_reverse_event_clears_caches(self):
        with patched_permission_caches() as mocks:
            self.send("pre_add", reverse=True, raw=False)
        self.assertCachesClearedFor(*mocks, self.user)

    def test_missing_raw_argument_clears_caches(self):
        """Django < 6.1 does not send ``raw`` at all; the default must not skip work."""
        with patched_permission_caches() as mocks:
            self.send("pre_add")
        self.assertCachesClearedFor(*mocks, self.user)

    def test_other_actions_are_still_ignored(self):
        for action in ("post_add", "post_remove", "pre_clear", "post_clear"):
            with self.subTest(action=action):
                with patched_permission_caches() as mocks:
                    self.send(action, raw=False)
                self.assertNoCacheInvalidation(*mocks)


class SaveRawSignalTests(PermissionCacheAssertionsMixin, CMSTestCase):
    """``pre_save``/``post_save`` receivers must ignore fixture loading events."""

    def setUp(self):
        super().setUp()
        self.user = self._create_user("raw-user", is_staff=True)
        self.group = Group.objects.create(name="raw-group")

    def assertIgnoresRaw(self, receiver, **kwargs):
        with patched_permission_caches() as mocks:
            with self.assertNumQueries(0):
                receiver(raw=True, **kwargs)
        self.assertNoCacheInvalidation(*mocks)

    def test_pre_save_user_ignores_raw(self):
        self.assertIgnoresRaw(permission_signals.pre_save_user, instance=self.user)

    def test_pre_save_group_ignores_raw(self):
        # Without the guard this would iterate ``instance.user_set.all()``.
        self.assertIgnoresRaw(permission_signals.pre_save_group, instance=self.group)

    def test_pre_save_pagepermission_ignores_raw(self):
        instance = PagePermission(user=self.user, group=self.group)
        self.assertIgnoresRaw(permission_signals.pre_save_pagepermission, instance=instance)

    def test_pre_save_globalpagepermission_ignores_raw(self):
        instance = GlobalPagePermission(user=self.user, group=self.group)
        self.assertIgnoresRaw(permission_signals.pre_save_globalpagepermission, instance=instance)

    def test_post_save_user_ignores_raw(self):
        self.assertIgnoresRaw(permission_signals.post_save_user, instance=self.user, created=True)

    def test_post_save_user_group_ignores_raw(self):
        self.assertIgnoresRaw(permission_signals.post_save_user_group, instance=self.group, created=True)

    def test_pre_save_user_still_clears_caches(self):
        with patched_permission_caches() as mocks:
            permission_signals.pre_save_user(instance=self.user, raw=False)
        self.assertCachesClearedFor(*mocks, self.user)

    def test_pre_save_group_still_clears_caches(self):
        self.user.groups.add(self.group)
        with patched_permission_caches() as mocks:
            permission_signals.pre_save_group(instance=self.group, raw=False)
        self.assertCachesClearedFor(*mocks, self.user)


class LoadDataPermissionSignalTests(PermissionCacheAssertionsMixin, CMSTestCase):
    """End-to-end check of the ``loaddata`` path."""

    def _dump_users_and_groups(self):
        output = StringIO()
        call_command(
            "dumpdata",
            "auth.Group",
            f"{User._meta.app_label}.{User._meta.model_name}",
            indent=2,
            stdout=output,
        )
        handle, fixture = tempfile.mkstemp(suffix=".json")
        os.close(handle)
        self.addCleanup(os.unlink, fixture)
        with open(fixture, "w", encoding="utf-8") as fixture_file:
            fixture_file.write(output.getvalue())
        return fixture

    def test_loaddata_restores_user_groups(self):
        user = self._create_user("fixture-user", is_staff=True)
        group = Group.objects.create(name="fixture-group")
        user.groups.add(group)
        user_pk, group_pk = user.pk, group.pk

        fixture = self._dump_users_and_groups()
        user.delete()
        group.delete()

        with patched_permission_caches():
            call_command("loaddata", fixture, verbosity=0)

        reloaded = User.objects.get(pk=user_pk)
        self.assertEqual(list(reloaded.groups.values_list("pk", flat=True)), [group_pk])

    @unittest.skipUnless(M2M_CHANGED_SENDS_RAW, "Django < 6.1 does not forward raw=True to m2m_changed")
    def test_loaddata_does_not_invalidate_permission_caches(self):
        user = self._create_user("fixture-user", is_staff=True)
        group = Group.objects.create(name="fixture-group")
        user.groups.add(group)

        fixture = self._dump_users_and_groups()
        user.delete()
        group.delete()

        with patched_permission_caches() as mocks:
            call_command("loaddata", fixture, verbosity=0)
        self.assertNoCacheInvalidation(*mocks)
