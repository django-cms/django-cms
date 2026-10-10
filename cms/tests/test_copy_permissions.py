from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sites.models import Site
from django.test import override_settings

from cms.api import add_plugin, create_page
from cms.cache.permissions import get_permission_cache, set_permission_cache
from cms.constants import PAGE_TYPES_ID
from cms.models import (
    ACCESS_CHILDREN,
    ACCESS_PAGE,
    ACCESS_PAGE_AND_DESCENDANTS,
    CMSPlugin,
    GlobalPagePermission,
    Page,
    PageContent,
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

    def test_copy_permissions_invalidates_permission_caches(self):
        self.add_page_permission(self.actor, self.source, can_change=True, grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_change_page(self.actor, self.source))

        copied = self.source.copy(
            self.source.site,
            parent_page=self.target,
            permissions=True,
            user=self.actor,
        )

        self.assertTrue(page_permissions.user_can_change_page(self.actor, copied))

    def test_copy_permissions_invalidates_another_users_cached_actions(self):
        recipient = self._create_user("recipient", is_staff=True, is_superuser=False)
        self.add_permission(recipient, "change_page")
        self.add_page_permission(recipient, self.source, can_change=True, grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_change_page(recipient, self.source))

        copied = self.source.copy(
            self.source.site,
            parent_page=self.target,
            permissions=True,
            user=self.actor,
        )

        self.assertTrue(page_permissions.user_can_change_page(recipient, copied))

    def test_copy_permissions_invalidates_cache_again_on_commit(self):
        self.add_page_permission(self.actor, self.source, can_change=True, grant_on=ACCESS_PAGE)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.source.copy(
                self.source.site,
                parent_page=self.target,
                permissions=True,
                user=self.actor,
            )
            # Simulate a concurrent request caching pre-commit permission rows.
            set_permission_cache(self.actor, self.source.site, "change_page", [])
            self.assertEqual(get_permission_cache(self.actor, self.source.site, "change_page"), [])

        self.assertEqual(len(callbacks), 1)
        self.assertIsNone(get_permission_cache(self.actor, self.source.site, "change_page"))

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


@override_settings(CMS_PERMISSION=True, CMS_PUBLIC_FOR="all")
class MovePermissionsTests(CMSTestCase):
    """A moved subtree leaves the ancestors that restricted it behind."""

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
        self.ancestor = create_page("ancestor", "nav_playground.html", "en")
        self.add_page_permission(self.admin, self.ancestor, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        self.source = create_page("source", "nav_playground.html", "en", parent=self.ancestor)
        self.secret = create_page("secret", "nav_playground.html", "en", parent=self.source)
        self.marker = "CONFIDENTIAL-MOVE-REGRESSION"
        add_plugin(self.secret.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)

    def move(self, page=None, target=None, position=0):
        page = page or self.source
        with self.login_user_context(self.actor):
            response = self.client.post(
                self.get_admin_url(Page, "move_page", page.pk),
                {"id": page.pk, "position": position, "target": (target or self.target).pk},
            )
        # Permission checks after the POST should use a fresh request's user.
        self.actor = type(self.actor).objects.get(pk=self.actor.pk)
        return response

    def grant_source(self, grant_on=ACCESS_PAGE_AND_DESCENDANTS):
        return self.add_page_permission(
            self.actor, self.source, can_change=True, can_move_page=True, grant_on=grant_on
        )

    def test_move_preserves_inherited_restriction(self):
        """The editor of a restricted branch cannot publish it by moving it."""
        self.grant_source()
        self.assertTrue(page_permissions.user_can_view_page(self.actor, self.secret))

        response = self.move()
        self.assertEqual(response.json().get("status", 200), 200)

        source = Page.objects.get(pk=self.source.pk)
        secret = Page.objects.get(pk=self.secret.pk)
        self.assertEqual(source.parent_id, self.target.pk)
        for page in (source, secret):
            self.assertTrue(page.has_view_restrictions(page.site))
            self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), page))
            self.assertEqual(self.client.get(page.get_absolute_url()).status_code, 404)
        with self.login_user_context(self.admin):
            self.assertContains(self.client.get(secret.get_absolute_url()), self.marker)

    def test_move_grants_no_editing_privileges(self):
        """Only ``can_view`` is materialized, never the ancestor's other flags."""
        self.add_page_permission(self.admin, self.ancestor, can_change=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        self.grant_source()
        self.move()

        source = Page.objects.get(pk=self.source.pk)
        self.assertTrue(source.pagepermission_set.filter(user=self.admin, can_view=True).exists())
        # The actor's own grant stays; the ancestor's can_change is not imported.
        self.assertFalse(source.pagepermission_set.filter(user=self.admin, can_change=True).exists())

    def test_move_keeps_unreadable_descendant_hidden(self):
        """The mover may not read ``secret``; the move must not change that."""
        self.grant_source(grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, self.source))
        self.assertFalse(page_permissions.user_can_view_page(self.actor, self.secret))

        response = self.move()
        self.assertEqual(response.json().get("status", 200), 200)

        secret = Page.objects.get(pk=self.secret.pk)
        self.assertFalse(page_permissions.user_can_view_page(self.actor, secret))
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), secret))
        self.assertEqual(self.client.get(secret.get_absolute_url()).status_code, 404)

    def test_destination_change_grant_cannot_expose_unreadable_descendant(self):
        """A destination grant would widen access, so the move is refused."""
        self.grant_source(grant_on=ACCESS_PAGE)
        self.target_permission.grant_on = ACCESS_PAGE_AND_DESCENDANTS
        self.target_permission.save()

        response = self.move()
        self.assertEqual(response.json()["status"], 403)
        self.assertEqual(Page.objects.get(pk=self.source.pk).parent_id, self.ancestor.pk)

    def test_destination_view_grant_cannot_expose_unreadable_descendant(self):
        self.grant_source(grant_on=ACCESS_PAGE)
        self.add_page_permission(self.actor, self.target, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)

        response = self.move()
        self.assertEqual(response.json()["status"], 403)
        self.assertEqual(Page.objects.get(pk=self.source.pk).parent_id, self.ancestor.pk)

    def test_move_inside_restricted_branch_adds_no_permissions(self):
        """Reordering inside the branch keeps inheritance, so nothing is copied."""
        self.grant_source()
        self.add_page_permission(self.actor, self.ancestor, can_add=True, can_change=True,
                                 grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        count = PagePermission.objects.count()

        response = self.move(target=self.ancestor)
        self.assertEqual(response.json().get("status", 200), 200)

        source = Page.objects.get(pk=self.source.pk)
        self.assertEqual(PagePermission.objects.count(), count)
        self.assertTrue(source.has_view_restrictions(source.site))

    def test_move_into_restricted_branch_adds_no_permissions(self):
        """An unrestricted page moved into a restricted branch inherits, no rows."""
        public = create_page("public", "nav_playground.html", "en")
        self.add_page_permission(self.actor, public, can_change=True, can_move_page=True, grant_on=ACCESS_PAGE)
        self.add_page_permission(self.actor, self.ancestor, can_add=True, can_change=True,
                                 grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        count = PagePermission.objects.count()

        response = self.move(page=public, target=self.ancestor)
        self.assertEqual(response.json().get("status", 200), 200)

        public = Page.objects.get(pk=public.pk)
        self.assertEqual(PagePermission.objects.count(), count)
        self.assertTrue(public.has_view_restrictions(public.site))
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), public))

    def test_move_of_unrestricted_page_adds_no_permissions(self):
        public = create_page("public", "nav_playground.html", "en")
        self.add_page_permission(self.actor, public, can_change=True, can_move_page=True, grant_on=ACCESS_PAGE)
        count = PagePermission.objects.count()

        response = self.move(page=public)
        self.assertEqual(response.json().get("status", 200), 200)

        public = Page.objects.get(pk=public.pk)
        self.assertEqual(PagePermission.objects.count(), count)
        self.assertFalse(public.has_view_restrictions(public.site))
        self.assertEqual(self.client.get(public.get_absolute_url()).status_code, 200)


@override_settings(CMS_PERMISSION=True, CMS_PUBLIC_FOR="all")
class DuplicatePermissionsTests(CMSTestCase):
    """``Duplicate`` copies a single page; its restrictions come along."""

    def setUp(self):
        super().setUp()
        self.admin = self.get_superuser()
        self.actor = self.get_staff_user_with_no_permissions()
        for codename in ("add_page", "change_page", "add_text", "change_text"):
            self.add_permission(self.actor, codename)
        self.target = create_page("target", "nav_playground.html", "en")
        self.add_page_permission(self.actor, self.target, can_add=True, can_change=True, grant_on=ACCESS_PAGE)
        self.marker = "CONFIDENTIAL-DUPLICATE-REGRESSION"

    def duplicate(self, source):
        content = source.get_admin_content("en")
        endpoint = self.get_admin_url(PageContent, "duplicate", content.pk)
        with self.login_user_context(self.actor):
            response = self.client.post(
                f"{endpoint}?parent_page={self.target.pk}",
                {
                    "title": "duplicate",
                    "slug": "duplicate",
                    "template": "nav_playground.html",
                    "language": "en",
                    "source": source.pk,
                    "parent_page": self.target.pk,
                    "_save": 1,
                },
            )
        self.actor = type(self.actor).objects.get(pk=self.actor.pk)
        return response, self.target.get_child_pages().first()

    def test_duplicate_preserves_own_restriction(self):
        source = create_page("source", "nav_playground.html", "en")
        add_plugin(source.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)
        self.add_page_permission(self.admin, source, can_view=True, grant_on=ACCESS_PAGE)
        self.add_page_permission(self.actor, source, can_view=True, can_change=True, grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, source))

        response, copy = self.duplicate(source)
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(copy)
        self.assertTrue(copy.has_view_restrictions(copy.site))
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), copy))
        self.assertEqual(self.client.get(copy.get_absolute_url()).status_code, 404)
        self.assertFalse(copy.pagepermission_set.filter(can_change=True).exists())
        with self.login_user_context(self.admin):
            self.assertContains(self.client.get(copy.get_absolute_url()), self.marker)

    def test_duplicate_preserves_inherited_restriction(self):
        ancestor = create_page("ancestor", "nav_playground.html", "en")
        self.add_page_permission(self.admin, ancestor, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        self.add_page_permission(
            self.actor, ancestor, can_view=True, can_change=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS,
        )
        source = create_page("source", "nav_playground.html", "en", parent=ancestor)
        add_plugin(source.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)

        response, copy = self.duplicate(source)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(copy.has_view_restrictions(copy.site))
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), copy))
        self.assertEqual(self.client.get(copy.get_absolute_url()).status_code, 404)
        # A page added below the copy stays protected, as it would below the source.
        child = create_page("child", "nav_playground.html", "en", parent=copy)
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), child))

    def test_duplicate_requires_change_permission_on_source(self):
        # Frontend view rights are not enough: ``Page.copy()`` reads the admin
        # content of the source, which the admin only shows to users who may
        # change the page.
        source = create_page("source", "nav_playground.html", "en")
        add_plugin(source.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, source))
        self.assertFalse(page_permissions.user_can_change_page(self.actor, source))

        response, copy = self.duplicate(source)
        self.assertEqual(response.status_code, 403)
        self.assertIsNone(copy)

    def test_duplicate_of_unrestricted_page_adds_no_permissions(self):
        source = create_page("source", "nav_playground.html", "en")
        add_plugin(source.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)
        self.add_page_permission(self.actor, source, can_change=True, grant_on=ACCESS_PAGE)
        count = PagePermission.objects.count()

        response, copy = self.duplicate(source)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PagePermission.objects.count(), count)
        self.assertFalse(copy.has_view_restrictions(copy.site))
        self.assertContains(self.client.get(copy.get_absolute_url()), self.marker)


@override_settings(
    CMS_PERMISSION=True, CMS_PUBLIC_FOR="all",
    CMS_LANGUAGES={"default": {"fallbacks": ["en"], "public": True}},
)
class DuplicateSitePermissionsTests(CMSTestCase):
    """Duplicate must enforce both source scope and destination permissions."""

    def setUp(self):
        super().setUp()
        self.forbidden_site = Site.objects.get_current()
        self.forbidden_site.domain = "forbidden.example"
        self.forbidden_site.save()
        self.allowed_site = Site.objects.create(domain="allowed.example", name="Allowed")
        self.allowed = create_page("allowed", "nav_playground.html", "en", site=self.allowed_site)
        self.forbidden = create_page("forbidden", "nav_playground.html", "en", site=self.forbidden_site)
        self.actor = self.get_staff_user_with_no_permissions()
        for codename in ("add_page", "change_page", "view_page"):
            self.add_permission(self.actor, codename)
        grant = GlobalPagePermission.objects.create(user=self.actor, can_add=True, can_change=True)
        grant.sites.add(self.allowed_site)
        site_settings = override_settings(
            SITE_ID=None,
            ALLOWED_HOSTS=["allowed.example", "forbidden.example", "testserver"],
        )
        site_settings.enable()
        self.addCleanup(site_settings.disable)
        # With ``SITE_ID=None`` the site is resolved from ``Host`` through the
        # process-wide ``SITE_CACHE``. Backends that do not reuse primary keys
        # across tests (PostgreSQL, MySQL) would otherwise serve a stale
        # ``allowed.example`` site from an earlier test.
        Site.objects.clear_cache()
        self.addCleanup(Site.objects.clear_cache)

    def duplicate(self, selected_site, site_in, host, query_parent=None, body_parent=None, source=None):
        # Keep the URL object and the default source on the editor's own site, so
        # destination tests fail on the destination check alone and the source
        # check cannot mask a write bypass.
        endpoint = self.get_admin_url(PageContent, "duplicate", self.allowed.get_admin_content("en").pk)
        if source is None:
            source = self.allowed
        query = {"language": "en"}
        data = {"title": "duplicate", "slug": f"duplicate-{(site_in or 'host').lower()}", "source": source.pk, "_save": 1}
        if query_parent:
            query["parent_page"] = query_parent.pk
        if body_parent:
            data["parent_page"] = body_parent.pk
        if site_in:
            (query if site_in == "GET" else data)["site"] = selected_site.pk
        query_string = "&".join(f"{key}={value}" for key, value in query.items())
        with self.login_user_context(self.actor):
            return self.client.post(f"{endpoint}?{query_string}", data, HTTP_HOST=host)

    def assert_source_rejected(self, source):
        counts = (Page.objects.count(), PageContent.objects.count(), CMSPlugin.objects.count())
        # Resolve the destination from Host, with no explicit site parameter.
        # The URL object and both parents belong to the editor's allowed site;
        # only the hidden source field is under the client's control.
        response = self.duplicate(
            self.allowed_site, None, "allowed.example", self.allowed, self.allowed, source=source,
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["adminform"].form
        self.assertIn("You do not have permission to copy this page.", form.errors["source"])
        self.assertEqual(
            (Page.objects.count(), PageContent.objects.count(), CMSPlugin.objects.count()), counts,
        )

    def test_unauthorized_cross_site_source_is_rejected(self):
        add_plugin(
            self.forbidden.get_placeholders("en").get(slot="body"),
            "TextPlugin", "en", body="CROSS-SITE-SOURCE-SECRET",
        )
        self.assert_source_rejected(self.forbidden)

    def test_authorized_cross_site_source_is_allowed(self):
        # Cross-site duplication stays possible for a user with rights on both
        # sites: the source is checked against *its* site, not the destination.
        grant = GlobalPagePermission.objects.create(user=self.actor, can_change=True)
        grant.sites.add(self.forbidden_site)
        marker = "CROSS-SITE-SOURCE-CONTENT"
        add_plugin(self.forbidden.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=marker)
        response = self.duplicate(
            self.allowed_site, None, "allowed.example", self.allowed, self.allowed,
            source=self.forbidden,
        )
        self.assertEqual(response.status_code, 302)
        copy = self.allowed.get_child_pages().get()
        self.assertEqual(copy.site_id, self.allowed_site.pk)
        self.assertContains(self.client.get(copy.get_absolute_url(), HTTP_HOST="allowed.example"), marker)

    def test_same_site_source_requires_change_permission(self):
        # An unreachable source must not become public through duplication, on
        # the same site too. This models a null URL path, not a djangocms-versioning
        # draft; both are admin-only content that ``Page.copy()`` would carry over.
        unreachable = create_page("unreachable", "nav_playground.html", "en", site=self.allowed_site)
        unreachable.urls.update(path=None)
        add_plugin(
            unreachable.get_placeholders("en").get(slot="body"),
            "TextPlugin", "en", body="SAME-SITE-SOURCE-SECRET",
        )
        # Keep add rights on the site, but confine change rights to ``allowed``.
        GlobalPagePermission.objects.filter(user=self.actor).update(can_change=False)
        PagePermission.objects.create(
            user=self.actor, page=self.allowed, can_add=True, can_change=True, grant_on=ACCESS_PAGE,
        )
        self.assert_source_rejected(unreachable)

    def test_duplicate_view_requires_permission_on_source(self):
        # ``GET`` on the endpoint of a content object the user may not open in the
        # admin fails at the view rather than rendering an unsubmittable form.
        endpoint = self.get_admin_url(PageContent, "duplicate", self.forbidden.get_admin_content("en").pk)
        with self.login_user_context(self.actor):
            response = self.client.get(f"{endpoint}?language=en", HTTP_HOST="allowed.example")
        self.assertEqual(response.status_code, 403)

    def test_same_site_source_is_allowed_with_host_resolution(self):
        marker = "SAME-SITE-SOURCE-CONTENT"
        add_plugin(self.allowed.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=marker)
        response = self.duplicate(
            self.allowed_site, None, "allowed.example", self.allowed, self.allowed,
            source=self.allowed,
        )
        self.assertEqual(response.status_code, 302)
        copy = self.allowed.get_child_pages().get()
        self.assertEqual(copy.site_id, self.allowed_site.pk)
        self.assertContains(self.client.get(copy.get_absolute_url(), HTTP_HOST="allowed.example"), marker)

    def test_unauthorized_site_selection_is_denied(self):
        for site_in in ("GET", "POST"):
            for host in ("allowed.example", "forbidden.example"):
                for parent in (None, self.forbidden):
                    with self.subTest(site_in=site_in, host=host, parent=parent):
                        count = Page.objects.count()
                        response = self.duplicate(self.forbidden_site, site_in, host, parent, parent)
                        self.assertEqual(response.status_code, 403)
                        self.assertEqual(Page.objects.count(), count)

    def test_allowed_query_parent_cannot_authorize_writes_to_another_site(self):
        for site_in in ("GET", "POST"):
            for host in ("allowed.example", "forbidden.example"):
                for parent in (None, self.forbidden):
                    with self.subTest(site_in=site_in, host=host, parent=parent):
                        count = Page.objects.count()
                        response = self.duplicate(
                            self.forbidden_site, site_in, host, self.allowed, parent,
                        )
                        self.assertEqual(response.status_code, 200)
                        form = response.context["adminform"].form
                        self.assertNotIn("source", form.errors)
                        self.assertIn("You do not have permission to add a page here.", form.errors["parent_page"])
                        self.assertEqual(Page.objects.count(), count)

    def test_authorized_site_can_be_selected_from_another_host(self):
        for site_in in ("GET", "POST"):
            with self.subTest(site_in=site_in):
                response = self.duplicate(
                    self.allowed_site, site_in, "forbidden.example", self.allowed, self.allowed,
                )
                self.assertEqual(response.status_code, 302)
                copy = Page.objects.get(pagecontent_set__slug=f"duplicate-{site_in.lower()}")
                self.assertEqual(copy.site_id, self.allowed_site.pk)
                self.assertEqual(copy.parent_id, self.allowed.pk)


@override_settings(CMS_PERMISSION=True, CMS_PUBLIC_FOR="all")
class PageTypeSourcePermissionsTests(CMSTestCase):
    """``Add page`` can copy a page type; its restrictions come along.

    Page types can no longer be created through the UI, but rows migrated from
    django CMS 3.x are still offered as ``source`` on the add form.
    """

    def setUp(self):
        super().setUp()
        self.admin = self.get_superuser()
        self.actor = self.get_staff_user_with_no_permissions()
        for codename in ("add_page", "change_page", "add_text", "change_text"):
            self.add_permission(self.actor, codename)
        self.target = create_page("target", "nav_playground.html", "en")
        self.add_page_permission(self.actor, self.target, can_add=True, can_change=True, grant_on=ACCESS_PAGE)
        self.marker = "CONFIDENTIAL-PAGE-TYPE-REGRESSION"

    def create_page_type(self, title, site=None):
        root = create_page("Page Types", "nav_playground.html", "en", site=site, reverse_id=PAGE_TYPES_ID)
        page_type = create_page(title, "nav_playground.html", "en", site=site, parent=root)
        Page.objects.filter(pk__in=(root.pk, page_type.pk)).update(is_page_type=True)
        add_plugin(page_type.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body=self.marker)
        return Page.objects.get(pk=page_type.pk)

    def add_from_source(self, source):
        endpoint = self.get_admin_url(PageContent, "add")
        with self.login_user_context(self.actor):
            response = self.client.post(
                f"{endpoint}?parent_page={self.target.pk}",
                {
                    "title": "from-page-type",
                    "slug": "from-page-type",
                    "template": "nav_playground.html",
                    "language": "en",
                    "source": source.pk,
                    "parent_page": self.target.pk,
                    "_save": 1,
                },
            )
        self.actor = type(self.actor).objects.get(pk=self.actor.pk)
        return response, self.target.get_child_pages().first()

    def assertAddDenied(self, source):
        counts = (Page.objects.count(), CMSPlugin.objects.count())
        response, copy = self.add_from_source(source)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(copy)
        self.assertEqual(counts, (Page.objects.count(), CMSPlugin.objects.count()))

    def test_rejects_page_type_user_cannot_view(self):
        source = self.create_page_type("secret-type")
        self.add_page_permission(self.admin, source, can_view=True, grant_on=ACCESS_PAGE)
        self.assertFalse(page_permissions.user_can_view_page(self.actor, source))
        self.assertAddDenied(source)

    @override_settings(
        CMS_LANGUAGES={
            1: [{"code": "en", "name": "English"}],
            2: [{"code": "en", "name": "English"}],
        }
    )
    def test_rejects_page_type_from_another_site(self):
        site = Site.objects.create(domain="other.example", name="Other")
        self.assertAddDenied(self.create_page_type("other-site-type", site=site))

    def test_rejects_page_type_root(self):
        source = self.create_page_type("visible-type")
        self.assertAddDenied(source.parent)

    def test_readable_page_type_can_be_used(self):
        source = self.create_page_type("visible-type")
        self.assertTrue(page_permissions.user_can_view_page(self.actor, source))

        response, copy = self.add_from_source(source)
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(copy)
        self.assertFalse(copy.is_page_type)
        self.assertContains(self.client.get(copy.get_absolute_url()), self.marker)

    def test_restricted_page_type_keeps_its_restriction(self):
        source = self.create_page_type("restricted-type")
        self.add_page_permission(self.admin, source, can_view=True, grant_on=ACCESS_PAGE)
        self.add_page_permission(self.actor, source, can_view=True, grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, source))

        response, copy = self.add_from_source(source)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(copy.has_view_restrictions(copy.site))
        self.assertFalse(page_permissions.user_can_view_page(AnonymousUser(), copy))
        self.assertEqual(self.client.get(copy.get_absolute_url()).status_code, 404)

    def test_rejects_source_when_adding_translation(self):
        source = self.create_page_type("restricted-type")
        self.add_page_permission(self.admin, source, can_view=True, grant_on=ACCESS_PAGE)
        # ``can_change`` lets the actor past the duplicate view's gate on the
        # source, so the form rule below is exercised on both endpoints.
        self.add_page_permission(self.actor, source, can_view=True, can_change=True, grant_on=ACCESS_PAGE)
        destination = create_page("destination", "nav_playground.html", "de")
        self.add_page_permission(self.actor, destination, can_change=True, grant_on=ACCESS_PAGE)
        self.assertTrue(page_permissions.user_can_view_page(self.actor, source))
        self.assertTrue(page_permissions.user_can_view_page(AnonymousUser(), destination))

        endpoints = (
            self.get_admin_url(PageContent, "add"),
            self.get_admin_url(PageContent, "duplicate", source.get_content_obj("en").pk),
        )
        data = {
            "cms_page": destination.pk,
            "source": source.pk,
            "language": "en",
            "title": "translation",
            "slug": "translation",
            "_save": 1,
        }
        models = (Page, PageContent, CMSPlugin, PagePermission)
        counts = tuple(model.objects.count() for model in models)
        with self.login_user_context(self.actor):
            for endpoint in endpoints:
                with self.subTest(endpoint=endpoint):
                    response = self.client.post(
                        f"{endpoint}?cms_page={destination.pk}&language=en&parent_page={self.target.pk}",
                        data,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("source", response.context["adminform"].form.errors)
                    self.assertFalse(destination.pagecontent_set.filter(language="en").exists())
                    self.assertEqual(counts, tuple(model.objects.count() for model in models))

            # Adding a translation without a source remains supported.
            data.pop("source")
            response = self.client.post(
                f"{endpoints[0]}?cms_page={destination.pk}&language=en&parent_page={self.target.pk}",
                data,
            )
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(self.client.get(destination.get_absolute_url("en")), self.marker)
