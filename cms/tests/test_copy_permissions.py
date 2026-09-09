from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sites.models import Site
from django.test import override_settings

from cms.api import add_plugin, create_page
from cms.models import (
    ACCESS_CHILDREN,
    ACCESS_PAGE,
    ACCESS_PAGE_AND_DESCENDANTS,
    CMSPlugin,
    Page,
    PagePermission,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils import page_permissions


@override_settings(CMS_PERMISSION=True, CMS_PUBLIC_FOR="all")
class CopyPermissionsTests(CMSTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.get_superuser()
        self.actor = self.get_staff_user_with_no_permissions()
        for codename in ("add_page", "change_page", "add_text", "change_text"):
            self.add_permission(self.actor, codename)
        self.target = create_page("target", "nav_playground.html", "en")
        self.target_permission = self.add_page_permission(
            self.actor, self.target, can_add=True, can_change=True, grant_on=ACCESS_PAGE
        )
        self.source = create_page("source", "nav_playground.html", "en")
        self.secret = create_page("secret", "nav_playground.html", "en", parent=self.source)
        self.add_page_permission(self.admin, self.secret, can_view=True, grant_on=ACCESS_PAGE)
        self.marker = "CONFIDENTIAL-COPY-REGRESSION"
        add_plugin(self.secret.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)

    def copy(self, copy_permissions, source=None, position=0):
        with self.login_user_context(self.actor):
            response = self.client.post(
                self.get_admin_url(Page, "copy_page", (source or self.source).pk),
                {"position": position, "target": self.target.pk, "copy_permissions": copy_permissions},
            )
        # Permission checks after the POST should use a fresh request's user.
        self.actor = type(self.actor).objects.get(pk=self.actor.pk)
        return response

    def assertCopyDenied(self, copy_permissions):
        counts = (Page.objects.count(), CMSPlugin.objects.count(), PagePermission.objects.count())
        response = self.copy(copy_permissions)
        self.assertEqual(response.json()["status"], 403)
        self.assertEqual(counts, (Page.objects.count(), CMSPlugin.objects.count(), PagePermission.objects.count()))

    def test_unreadable_descendant_requires_copy_permissions(self):
        self.assertTrue(page_permissions.user_can_view_page(self.actor, self.source))
        self.assertFalse(page_permissions.user_can_view_page(self.actor, self.secret))
        self.assertFalse(page_permissions.user_can_change_page(self.actor, self.secret))
        self.assertEqual(self.client.get(self.secret.get_absolute_url()).status_code, 404)
        self.assertCopyDenied("")

    def test_unreadable_descendant_can_be_copied_with_permissions(self):
        response = self.copy("on")
        self.assertEqual(response.status_code, 200)
        copied = Page.objects.get(pk=response.json()["id"]).get_child_pages().get()
        self.assertTrue(copied.has_view_restrictions(copied.site))
        self.assertFalse(page_permissions.user_can_view_page(self.actor, copied))
        self.assertEqual(self.client.get(copied.get_absolute_url()).status_code, 404)
        with self.login_user_context(self.admin):
            self.assertContains(self.client.get(copied.get_absolute_url()), self.marker)

    def test_destination_change_grant_cannot_expose_unreadable_descendant(self):
        self.target_permission.grant_on = ACCESS_PAGE_AND_DESCENDANTS
        self.target_permission.save()
        self.assertCopyDenied("on")

    def test_destination_view_grant_cannot_expose_unreadable_descendant(self):
        self.add_page_permission(self.actor, self.target, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        self.assertCopyDenied("on")

    def test_destination_group_grant_cannot_expose_unreadable_descendant(self):
        group = Group.objects.create(name="Destination viewers")
        self.actor.groups.add(group)
        self.add_page_permission(None, self.target, group=group, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        self.assertCopyDenied("on")

    @override_settings(
        CMS_LANGUAGES={
            1: [{"code": "en", "name": "English"}],
            2: [{"code": "en", "name": "English"}],
        }
    )
    def test_destination_site_global_grant_cannot_expose_unreadable_descendant(self):
        site = Site.objects.create(domain="destination.example", name="Destination")
        self.target = create_page("other-site", "nav_playground.html", "en", site=site)
        permission = self.add_global_permission(self.actor, can_add=True, can_change=True)
        permission.sites.set([site])
        self.assertFalse(page_permissions.user_can_view_page(self.actor, self.secret))
        with self.settings(SITE_ID=site.pk):
            self.assertCopyDenied("on")

    def test_unreadable_grandchild_requires_copy_permissions(self):
        self.secret.pagepermission_set.all().delete()
        grandchild = create_page("grandchild", "nav_playground.html", "en", parent=self.secret)
        self.add_page_permission(self.admin, grandchild, can_view=True, grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, self.secret))
        self.assertCopyDenied("")

    def test_destination_immediate_children_grant_does_not_expose_descendant(self):
        self.add_page_permission(self.actor, self.target, can_view=True, grant_on=ACCESS_CHILDREN)
        response = self.copy("on")
        self.assertEqual(response.status_code, 200)
        copied = Page.objects.get(pk=response.json()["id"]).get_child_pages().get()
        self.assertFalse(page_permissions.user_can_view_page(self.actor, copied))

    def test_copy_permissions_preserves_root_restriction(self):
        self.add_page_permission(self.actor, self.source, can_view=True, grant_on=ACCESS_PAGE)
        response = self.copy("on")
        self.assertEqual(response.status_code, 200)
        copied = Page.objects.get(pk=response.json()["id"])
        self.assertTrue(copied.pagepermission_set.filter(user=self.actor, can_view=True).exists())
        self.assertEqual(self.client.get(copied.get_absolute_url()).status_code, 404)

    def test_readable_descendants_can_be_copied_without_permissions(self):
        self.add_page_permission(self.actor, self.secret, can_view=True, grant_on=ACCESS_PAGE)
        response = self.copy("")
        self.assertEqual(response.status_code, 200)
        copied = Page.objects.get(pk=response.json()["id"]).get_child_pages().get()
        self.assertFalse(copied.has_view_restrictions(copied.site))
        self.assertContains(self.client.get(copied.get_absolute_url()), self.marker)

    def test_inherited_restrictions_survive_outside_source_subtree(self):
        ancestor = create_page("ancestor", "nav_playground.html", "en")
        source = create_page("nested-source", "nav_playground.html", "en", parent=ancestor)
        child = create_page("nested-child", "nav_playground.html", "en", parent=source)
        self.add_page_permission(self.admin, ancestor, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        self.add_page_permission(self.actor, ancestor, can_view=True, grant_on=ACCESS_CHILDREN)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, source))
        self.assertFalse(page_permissions.user_can_view_page(self.actor, child))
        response = self.copy("on", source=source)
        self.assertEqual(response.status_code, 200)
        copied = Page.objects.get(pk=response.json()["id"])
        copied_child = copied.get_child_pages().get()
        self.assertTrue(page_permissions.user_can_view_page(self.actor, copied))
        self.assertFalse(page_permissions.user_can_view_page(self.actor, copied_child))
        for page in (copied, copied_child):
            self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), page))
            self.assertTrue(PagePermission.objects.for_page(page).filter(user=self.admin, can_view=True).exists())
            self.assertFalse(page.pagepermission_set.filter(can_change=True).exists())
        added_child = create_page("later-child", "nav_playground.html", "en", parent=copied_child)
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), added_child))
        self.assertFalse(page_permissions.user_can_view_page(self.actor, added_child))

    def test_unreadable_root_is_still_rejected(self):
        response = self.copy("on", source=self.secret)
        self.assertEqual(response.json()["status"], 403)
