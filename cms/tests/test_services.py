from django.core.exceptions import PermissionDenied, ValidationError

from cms.api import add_plugin, create_page
from cms.core.services import plugins as plugin_services
from cms.core.services.permissions import PluginPermissions, get_permissions
from cms.models import Page, Placeholder, UserSettings
from cms.pages import services as page_services
from cms.pages.permissions import PagePermissions, get_page_permissions
from cms.shared.operations import OperationContext
from cms.signals import post_placeholder_operation, pre_placeholder_operation
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
