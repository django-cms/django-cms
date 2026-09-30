from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import override_settings

from cms import operations
from cms.api import add_plugin, create_page
from cms.core.services import plugins as plugin_services
from cms.core.services.permissions import PluginPermissions, get_permissions
from cms.models import GlobalPagePermission, Page, PageContent, PagePermission, PageType, Placeholder, UserSettings
from cms.pages import services as page_services
from cms.pages.permissions import PagePermissions, get_page_permissions
from cms.shared import checks
from cms.shared.checks import can
from cms.shared.operations import OperationContext
from cms.signals import (
    PAGE_OPERATION_SIGNALS,
    post_obj_operation,
    post_placeholder_operation,
    pre_obj_operation,
    pre_placeholder_operation,
)
from cms.test_utils.testcases import CMSTestCase


class OperationContextTest(CMSTestCase):
    def test_from_request_parses_the_originating_path(self):
        request = self.get_request("/en/admin/cms/placeholder/?cms_path=/en/some-page/")
        request.user = self.get_superuser()

        context = OperationContext.from_request(request)

        self.assertEqual(context.origin, "/en/some-page/")
        self.assertEqual(context.language, "en")
        self.assertIs(context.request, request)
        self.assertTrue(context.emit_signals)

    def test_language_query_on_the_origin_wins(self):
        """``?language`` lets an editor view one language at another's URL."""
        request = self.get_request("/en/admin/?cms_path=/en/some-page/%3Flanguage%3Dde")
        request.user = self.get_superuser()
        request.GET = request.GET.copy()
        request.GET["cms_path"] = "/en/some-page/?language=de"

        self.assertEqual(OperationContext.from_request(request).language, "de")

    def test_placeholder_request_without_cms_path_stays_silent(self):
        """The long-standing shim: no cms_path means no operation signals."""
        request = self.get_request("/en/admin/cms/placeholder/")
        request.user = self.get_superuser()

        with self.assertWarns(UserWarning):
            context = OperationContext.from_placeholder_request(request)

        self.assertFalse(context.emit_signals)
        self.assertIsNone(context.origin)

    def test_plain_request_without_cms_path_still_emits(self):
        """Only the placeholder endpoints use cms_path; page endpoints do not."""
        request = self.get_request("/en/admin/cms/page/1/set-home/")
        request.user = self.get_superuser()

        context = OperationContext.from_request(request)

        self.assertTrue(context.emit_signals)
        self.assertIsNone(context.origin)


class RequestFreeServiceTest(CMSTestCase):
    """Services run outside the admin -- no request, no HTTP, no admin instance."""

    def setUp(self):
        super().setUp()
        self.user = self.get_superuser()
        self.page = create_page("home", "nav_playground.html", "en")
        self.placeholder = self.page.get_placeholders("en").get(slot="body")

    def _context(self, **kwargs):
        return OperationContext(user=self.user, language="en", origin="/en/", **kwargs)

    def test_add_page_service_creates_content_without_a_request(self):
        content = page_services.add_page(
            site=self.page.site,
            parent_page=self.page,
            source=None,
            language="en",
            content_data={"title": "new", "slug": "new", "path": "home/new", "template": "nav_playground.html"},
            context=self._context(),
        )
        self.assertEqual(content.page.parent_id, self.page.pk)
        self.assertEqual(content.title, "new")

    def test_page_write_services_reject_an_unprivileged_caller(self):
        actor = self.get_staff_user_with_no_permissions()
        context = OperationContext(user=actor, language="en")
        count = Page.objects.count()
        with self.assertRaises(PermissionDenied):
            page_services.add_page(
                site=self.page.site, parent_page=self.page, source=None, language="en",
                content_data={"title": "new", "slug": "new", "path": "home/new", "template": "nav_playground.html"},
                context=context,
            )
        with self.assertRaises(PermissionDenied):
            page_services.add_translation(
                self.page, language="de",
                content_data={"title": "Neu", "slug": "neu", "path": "neu", "template": "nav_playground.html"},
                context=context,
            )
        content = self.page.get_admin_content("en")
        with self.assertRaises(PermissionDenied):
            page_services.change_page_content(
                content, data={"title": "changed"}, context=context,
            )
        with self.assertRaises(PermissionDenied):
            page_services.change_advanced_settings(self.page, context=context)
        with self.assertRaises(PermissionDenied):
            page_services.save_page_permissions(self.page, context=context)
        self.assertEqual(Page.objects.count(), count)
        content.refresh_from_db()
        self.assertEqual(content.title, "home")

    def test_change_services_only_write_supported_fields(self):
        other_site = Site.objects.create(domain="other.example", name="Other")
        content = self.page.get_admin_content("en")
        with self.assertRaises(ValidationError):
            page_services.change_page_content(
                content, data={"page": self.page}, context=self._context(),
            )
        self.page.site = other_site
        self.page.login_required = True
        page_services.change_advanced_settings(self.page, context=self._context())
        self.page.refresh_from_db()
        self.assertNotEqual(self.page.site_id, other_site.pk)
        self.assertTrue(self.page.login_required)

    def test_change_advanced_settings_reloads_urls_for_any_apphook_change(self):
        # The caller does not have to say what changed: the service compares
        # with the stored page.
        self.page.application_urls = "SampleApp"
        with patch("cms.pages.services.set_restart_trigger") as restart:
            page_services.change_advanced_settings(self.page, context=self._context())
        restart.assert_called_once()

        self.page.refresh_from_db()
        self.assertEqual(self.page.application_urls, "SampleApp")
        self.page.login_required = True
        with patch("cms.pages.services.set_restart_trigger") as restart:
            page_services.change_advanced_settings(self.page, context=self._context())
        restart.assert_not_called()

    def test_change_page_content_reloads_urls_when_the_path_changes(self):
        self.page.update(application_urls="SampleApp")
        content = self.page.get_admin_content("en")

        with patch("cms.pages.services.set_restart_trigger") as restart:
            page_services.change_page_content(content, data={"title": "renamed"}, context=self._context())
        restart.assert_not_called()

        # An overwritten URL changes the path as much as a new slug does.
        with patch("cms.pages.services.set_restart_trigger") as restart:
            page_services.change_page_content(
                content, data={"overwrite_url": "elsewhere"}, context=self._context()
            )
        restart.assert_called_once()
        self.assertEqual(self.page.get_path("en", fallback=False), "elsewhere")

    def test_permission_services_reject_unprivileged_caller(self):
        actor = self.get_staff_user_with_no_permissions()
        context = OperationContext(user=actor)
        with self.assertRaises(PermissionDenied):
            page_services.set_user_permissions({"can_add_page": True}, actor, context=context)
        grant = GlobalPagePermission(user=actor, can_add=True, can_change=True)
        with self.assertRaises(PermissionDenied):
            page_services.save_global_page_permission(grant, sites=[Site.objects.get_current()], context=context)
        self.assertFalse(GlobalPagePermission.objects.filter(user=actor).exists())

    def test_permission_services_apply_and_remove_grants(self):
        actor = self.get_staff_user_with_no_permissions()
        page_grant = PagePermission(user=actor, page=self.page)
        page_services.save_page_permissions(self.page, save=[page_grant], context=self._context())
        self.assertTrue(PagePermission.objects.filter(pk=page_grant.pk).exists())
        page_services.save_page_permissions(self.page, delete=[page_grant], context=self._context())
        self.assertFalse(PagePermission.objects.filter(pk=page_grant.pk).exists())

        global_grant = GlobalPagePermission(user=actor)
        site = Site.objects.get_current()
        page_services.save_global_page_permission(global_grant, sites=[site], context=self._context())
        self.assertEqual(list(global_grant.sites.all()), [site])
        page_services.delete_global_page_permissions([global_grant], context=self._context())
        self.assertFalse(GlobalPagePermission.objects.filter(pk=global_grant.pk).exists())

    def test_move_plugin_without_a_request(self):
        first = add_plugin(self.placeholder, "LinkPlugin", "en", name="first")
        second = add_plugin(self.placeholder, "LinkPlugin", "en", name="second")

        plugin_services.move_plugin(
            second.cmsplugin_ptr,
            target_position=1,
            context=self._context(),
        )

        order = self.placeholder.get_plugin_tree_order(language="en")
        self.assertEqual(order, [second.pk, first.pk])

    def test_signals_fire_with_request_none(self):
        """Receivers get ``request=None`` for a programmatic call, and must cope."""
        plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="one")
        seen = []

        def receiver(sender, **kwargs):
            seen.append(kwargs)

        pre_placeholder_operation.connect(receiver, dispatch_uid="svc-test-pre")
        post_placeholder_operation.connect(receiver, dispatch_uid="svc-test-post")
        try:
            plugin_services.move_plugin(plugin.cmsplugin_ptr, target_position=1, context=self._context())
        finally:
            pre_placeholder_operation.disconnect(dispatch_uid="svc-test-pre")
            post_placeholder_operation.disconnect(dispatch_uid="svc-test-post")

        self.assertEqual(len(seen), 2)
        for kwargs in seen:
            self.assertIsNone(kwargs["request"])
            self.assertEqual(kwargs["origin"], "/en/")
            self.assertEqual(kwargs["language"], "en")
        self.assertEqual(seen[0]["token"], seen[1]["token"])

    def test_silenced_context_emits_nothing(self):
        plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="one")
        seen = []
        pre_placeholder_operation.connect(lambda sender, **kw: seen.append(kw), dispatch_uid="svc-test-quiet")
        try:
            plugin_services.move_plugin(
                plugin.cmsplugin_ptr,
                target_position=1,
                context=self._context(emit_signals=False),
            )
        finally:
            pre_placeholder_operation.disconnect(dispatch_uid="svc-test-quiet")

        self.assertEqual(seen, [])

    def test_delete_plugin_without_a_request(self):
        plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="doomed")

        tree_order = plugin_services.delete_plugin(plugin.cmsplugin_ptr, context=self._context())

        self.assertEqual(tree_order, [])
        self.assertFalse(self.placeholder.get_plugins("en").exists())

    def test_clear_placeholder_without_a_request(self):
        add_plugin(self.placeholder, "LinkPlugin", "en", name="one")
        add_plugin(self.placeholder, "LinkPlugin", "en", name="two")

        plugin_services.clear_placeholder(self.placeholder, "en", context=self._context())

        self.assertFalse(self.placeholder.get_plugins("en").exists())


class PluginParentGuardTest(CMSTestCase):
    """The parent a service puts a plugin under is checked, as the admin view does."""

    def setUp(self):
        super().setUp()
        self.context = OperationContext(user=self.get_superuser(), language="en")
        page = create_page("home", "nav_playground.html", "en")
        placeholders = page.get_placeholders("en")
        self.body = placeholders.get(slot="body")
        self.other = placeholders.get(slot="right-column")
        self.sent = []
        pre_placeholder_operation.connect(self.receive)
        self.addCleanup(pre_placeholder_operation.disconnect, self.receive)

    def receive(self, **kwargs):
        self.sent.append(kwargs["operation"])

    def test_move_refuses_a_parent_in_another_placeholder(self):
        plugin = add_plugin(self.body, "TextPlugin", "en", body="moved")
        foreign = add_plugin(self.other, "MultiColumnPlugin", "en")

        with self.assertRaises(ValidationError):
            plugin_services.move_plugin(plugin, 0, target_parent=foreign, context=self.context)

        plugin.refresh_from_db()
        self.assertIsNone(plugin.parent_id)
        self.assertEqual(self.sent, [])

    def test_move_refuses_a_parent_in_another_language(self):
        plugin = add_plugin(self.body, "TextPlugin", "en", body="moved")
        german = add_plugin(self.body, "MultiColumnPlugin", "de")

        with self.assertRaises(ValidationError):
            plugin_services.move_plugin(plugin, 0, target_parent=german, context=self.context)

    def test_move_refuses_its_own_descendant(self):
        parent = add_plugin(self.body, "MultiColumnPlugin", "en")
        child = add_plugin(self.body, "ColumnPlugin", "en", target=parent)

        with self.assertRaisesMessage(ValidationError, "cannot be moved inside itself"):
            plugin_services.move_plugin(parent, 0, target_parent=child, context=self.context)

    def test_move_accepts_a_parent_in_the_target_placeholder(self):
        plugin = add_plugin(self.body, "TextPlugin", "en", body="moved")
        parent = add_plugin(self.other, "MultiColumnPlugin", "en")

        plugin_services.move_plugin(
            plugin, 1, target_placeholder=self.other, target_parent=parent, context=self.context
        )

        plugin.refresh_from_db()
        self.assertEqual((plugin.placeholder_id, plugin.parent_id), (self.other.pk, parent.pk))

    def test_paste_refuses_a_parent_in_another_placeholder(self):
        plugin = add_plugin(self.body, "TextPlugin", "en", body="copied")
        foreign = add_plugin(self.other, "MultiColumnPlugin", "en")

        with self.assertRaises(ValidationError):
            plugin_services.paste_plugin(
                plugin, "en", self.body, 1, target_parent=foreign, context=self.context
            )
        self.assertEqual(self.sent, [])


class GrantServiceTest(CMSTestCase):
    """The permission-grant services run registered checks, and cms.api runs as the system."""

    def setUp(self):
        super().setUp()
        self.page = create_page("home", "nav_playground.html", "en")
        self.site = Site.objects.get_current()
        self.admin = OperationContext(user=self.get_superuser())
        self.staff = OperationContext(user=self.get_staff_user_with_no_permissions())

    def test_set_user_permissions_needs_a_context(self):
        with self.assertRaises(TypeError):
            page_services.set_user_permissions({"can_add_page": True}, self.staff.user)

    def test_a_system_context_grants_without_permission_checks(self):
        target = self._create_user("target", is_staff=True)

        page_services.set_user_permissions(
            {"can_add_page": True}, target, context=OperationContext.system("tests")
        )

        self.assertTrue(target.user_permissions.filter(codename="add_page").exists())

    def test_cms_api_creates_page_users_as_the_system(self):
        from cms.api import create_page_user

        user = self._create_user("created", is_staff=True)
        create_page_user(self.get_superuser(), user, can_add_page=True, can_change_page=True)

        self.assertTrue(user.user_permissions.filter(codename="add_page").exists())

    def test_dry_runs_for_grant_operations(self):
        grant = GlobalPagePermission(user=self.staff.user, can_add=True, can_change=True)
        verdict = can(operations.CHANGE_GLOBAL_PAGE_PERMISSION, self.staff, grant=grant, sites=[self.site])
        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.permissions.global_grant_grantable")
        self.assertTrue(can(operations.CHANGE_GLOBAL_PAGE_PERMISSION, self.admin, grant=grant, sites=[self.site]))

        # Nobody manages themselves ...
        verdict = can(operations.CHANGE_USER_PERMISSIONS, self.staff, obj=self.staff.user, data={})
        self.assertEqual(verdict.reasons[0].name, "cms.permissions.manage_user_or_group")
        # ... and only permissions one holds can be handed out, also to a new user.
        new_user = get_user_model()(username="new")
        verdict = can(operations.CHANGE_USER_PERMISSIONS, self.staff, obj=new_user, data={"can_add_page": True})
        self.assertEqual(verdict.reasons[0].name, "cms.permissions.grantable_user_permissions")

    def test_a_grant_of_another_page_is_refused(self):
        other = create_page("other", "nav_playground.html", "en")
        grant = PagePermission.objects.create(user=self.staff.user, page=other, can_view=True)

        with self.assertRaisesMessage(ValidationError, "belongs to another page"):
            page_services.save_page_permissions(self.page, delete=[grant], context=self.admin)
        self.assertTrue(PagePermission.objects.filter(pk=grant.pk).exists())

    def test_deleting_global_grants_is_all_or_nothing(self):
        first = GlobalPagePermission.objects.create(user=self.staff.user)
        second = GlobalPagePermission.objects.create(user=self.get_superuser())
        # ``delete()`` clears the instance's pk, and a rollback does not restore it.
        ids = [first.pk, second.pk]

        def refuse_second(context, *, grant, **kwargs):
            if grant.pk == second.pk:
                raise PermissionDenied("Not this one")

        checks.register_check(
            operations.DELETE_GLOBAL_PAGE_PERMISSION, "tests.refuse_second", refuse_second, kind=checks.PERMISSION
        )
        self.addCleanup(checks._extensions[operations.DELETE_GLOBAL_PAGE_PERMISSION].pop, "tests.refuse_second")

        with self.assertRaises(PermissionDenied):
            page_services.delete_global_page_permissions([first, second], context=self.admin)
        self.assertEqual(GlobalPagePermission.objects.filter(pk__in=ids).count(), 2)


@override_settings(CMS_PERMISSION=True)
class PageGrantRecipientTest(CMSTestCase):
    """Editing rights on a page only go to users and groups the actor manages."""

    def setUp(self):
        super().setUp()
        self.page = create_page("home", "nav_playground.html", "en")
        delegate = self._create_user("delegate", is_staff=True, add_default_permissions=True)
        self.add_global_permission(delegate, can_change=True, can_change_permissions=True, can_view=True)
        self.context = OperationContext(user=delegate)

    def verdict(self, **flags):
        # The model's flags default to True; only the ones under test are set.
        grant = PagePermission(
            user=self.get_superuser(),
            page=self.page,
            **{**dict.fromkeys(PagePermission.get_all_permissions(), False), **flags},
        )
        return can(operations.CHANGE_PAGE_PERMISSIONS, self.context, page=self.page, save=[grant])

    def test_editing_rights_go_to_managed_users_only(self):
        # A flag the delegate holds, for a user they do not manage (a superuser).
        verdict = self.verdict(can_change_permissions=True)

        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.grant_recipients")

    def test_view_restrictions_may_name_anyone(self):
        verdict = self.verdict(can_view=True)

        self.assertNotIn("cms.pages.grant_recipients", [reason.name for reason in verdict.reasons])


class AddPageServiceTest(CMSTestCase):
    def setUp(self):
        super().setUp()
        self.site = Site.objects.get_current()
        self.context = OperationContext(user=self.get_superuser(), language="en")
        self.sent = []
        for signal in PAGE_OPERATION_SIGNALS:
            signal.connect(self.receive)
            self.addCleanup(signal.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append((signal, kwargs["operation"], kwargs.get("obj")))

    def add(self, **kwargs):
        options = {
            "site": self.site,
            "parent_page": None,
            "source": None,
            "language": "en",
            "content_data": {"title": "new", "slug": "new", "path": "new", "template": "nav_playground.html"},
            "context": self.context,
        }
        return page_services.add_page(**{**options, **kwargs})

    def test_is_announced_as_adding_a_translation(self):
        content = self.add()

        self.assertEqual(
            self.sent,
            [
                (pre_obj_operation, operations.ADD_PAGE_TRANSLATION, None),
                (post_obj_operation, operations.ADD_PAGE_TRANSLATION, content.page),
            ],
        )

    def test_a_refused_add_announces_nothing(self):
        staff = OperationContext(user=self.get_staff_user_with_no_permissions())
        with self.assertRaises(PermissionDenied):
            self.add(context=staff)
        self.assertEqual(self.sent, [])

    def test_page_types_get_the_page_types_root(self):
        self.assertIsNone(PageType.get_root_page(site=self.site))

        content = self.add(is_page_type=True, content_data={
            "title": "type", "slug": "type", "path": "page_types/type", "template": "nav_playground.html",
        })

        root = PageType.get_root_page(site=self.site)
        self.assertEqual(content.page.parent, root)
        self.assertTrue(content.page.is_page_type)
        self.assertTrue(root.has_translation("en"))

    def test_a_page_from_a_source_copies_it(self):
        source = create_page("source", "nav_playground.html", "en")
        add_plugin(source.get_placeholders("en").get(slot="body"), "TextPlugin", "en", body="copied")

        content = self.add(source=source)

        self.assertNotEqual(content.page.pk, source.pk)
        # Every slot exists once: the copy reuses the placeholders the new content got.
        slots = list(content.placeholders.values_list("slot", flat=True))
        self.assertEqual(sorted(slots), sorted(set(slots)))
        self.assertEqual(
            [plugin.get_bound_plugin().body for plugin in content.page.get_placeholders("en").get(slot="body").get_plugins("en")],
            ["copied"],
        )

    def test_a_source_the_user_may_not_copy_is_refused_before_anything_happens(self):
        source = create_page("source", "nav_playground.html", "en")

        class NoCopies(PagePermissions):
            def can_change_page(self, page):
                return page != source

        count = Page.objects.count()
        with self.assertRaises(PermissionDenied):
            self.add(source=source, permissions=NoCopies(self.context.user))
        self.assertEqual(Page.objects.count(), count)
        self.assertEqual(self.sent, [])


class ServicePermissionTest(CMSTestCase):
    """Services enforce, so a non-admin caller is checked the same way.

    This is what closes the gap left open in step 5: before, calling a service
    directly performed the operation for anybody.
    """

    def setUp(self):
        super().setUp()
        self.page = create_page("home", "nav_playground.html", "en")
        self.placeholder = self.page.get_placeholders("en").get(slot="body")
        self.plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="one").cmsplugin_ptr

    def _context(self, user):
        return OperationContext(user=user, language="en", origin="/en/")

    def test_service_denies_a_user_without_permission(self):
        staff = self.get_staff_user_with_no_permissions()

        with self.assertRaises(PermissionDenied):
            plugin_services.move_plugin(self.plugin, target_position=1, context=self._context(staff))

    def test_service_allows_a_user_with_permission(self):
        plugin_services.move_plugin(
            self.plugin, target_position=1, context=self._context(self.get_superuser())
        )

        self.assertEqual(self.placeholder.get_plugin_tree_order(language="en"), [self.plugin.pk])

    def test_delete_is_guarded_too(self):
        staff = self.get_staff_user_with_no_permissions()

        with self.assertRaises(PermissionDenied):
            plugin_services.delete_plugin(self.plugin, context=self._context(staff))

        self.assertTrue(self.placeholder.get_plugins("en").exists())

    def test_an_explicit_backend_overrides_the_default(self):
        """``permissions=`` is how the admin keeps its overridable hooks in charge."""

        class RefuseEverything(PluginPermissions):
            def can_move_plugin(self, plugin, target_placeholder):
                return False

        with self.assertRaises(PermissionDenied):
            plugin_services.move_plugin(
                self.plugin,
                target_position=1,
                context=self._context(self.get_superuser()),
                permissions=RefuseEverything(self.get_superuser()),
            )

    def test_default_backend_mirrors_the_admin_hooks(self):
        """A stock install must decide exactly as the admin used to."""
        superuser = self.get_superuser()
        permissions = get_permissions(superuser)

        self.assertTrue(permissions.can_move_plugin(self.plugin, self.placeholder))
        self.assertTrue(permissions.can_delete_plugin(self.plugin))
        self.assertTrue(permissions.can_edit_source(self.placeholder))
        self.assertEqual(
            permissions.can_clear_placeholder(self.placeholder, "en"),
            self.placeholder.has_clear_permission(superuser, ["en"]),
        )

    def test_clipboard_resolves_without_a_request(self):
        """The clipboard comes from UserSettings, not from a toolbar."""
        superuser = self.get_superuser()
        UserSettings.objects.create(
            user=superuser, language="en", clipboard=Placeholder.objects.create(slot="clipboard")
        )

        self.assertIsNotNone(get_permissions(superuser).clipboard)

    def test_no_user_settings_means_no_clipboard(self):
        self.assertIsNone(get_permissions(self.get_superuser()).clipboard)


class PageServicePermissionTest(CMSTestCase):
    """The pages half of the same guarantee: page services enforce too."""

    def setUp(self):
        super().setUp()
        self.page = create_page("home", "nav_playground.html", "en")

    def _context(self, user):
        return OperationContext(user=user, language="en", origin="/en/")

    def test_delete_page_denies_a_user_without_permission(self):
        staff = self.get_staff_user_with_no_permissions()

        with self.assertRaises(PermissionDenied):
            page_services.delete_page(self.page, context=self._context(staff))

        self.assertTrue(Page.objects.filter(pk=self.page.pk).exists())

    def test_set_home_denies_a_user_without_permission(self):
        other = create_page("other", "nav_playground.html", "en")
        staff = self.get_staff_user_with_no_permissions()

        with self.assertRaises(PermissionDenied):
            page_services.set_home(other, context=self._context(staff))

    def test_toggle_in_navigation_denies_a_user_without_permission(self):
        staff = self.get_staff_user_with_no_permissions()
        content = self.page.get_content_obj("en")

        with self.assertRaises(PermissionDenied):
            page_services.toggle_in_navigation(content, context=self._context(staff))

    def test_superuser_is_allowed(self):
        content = self.page.get_content_obj("en")
        before = content.in_navigation

        after = page_services.toggle_in_navigation(content, context=self._context(self.get_superuser()))

        self.assertNotEqual(before, after)

    def test_an_explicit_backend_overrides_the_default(self):
        class RefuseEverything(PagePermissions):
            def can_delete_page(self, page):
                return False

        with self.assertRaises(PermissionDenied):
            page_services.delete_page(
                self.page,
                context=self._context(self.get_superuser()),
                permissions=RefuseEverything(self.get_superuser()),
            )

    def test_default_backend_mirrors_the_admin_hooks(self):
        superuser = self.get_superuser()
        permissions = get_page_permissions(superuser)

        self.assertTrue(permissions.can_change_page(self.page))
        self.assertTrue(permissions.can_delete_page(self.page))
        self.assertTrue(permissions.can_view_page(self.page))
