from unittest.mock import patch

from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.utils.functional import Promise
from django.utils.translation import override as force_language

from cms import operations
from cms.api import add_plugin, create_page, create_page_content
from cms.cms_config import CMSCoreExtensions
from cms.core import checks as core_checks
from cms.core.plugin_pool import plugin_pool
from cms.core.services import plugins as plugin_services
from cms.models import CMSPlugin, Page, PageContent, Placeholder, UserSettings
from cms.pages import services as page_services
from cms.pages.admin.forms import MovePageForm
from cms.pages.admin.page import PageAdmin, PageContentAdmin
from cms.pages.permissions import AdminPageContentPermissions, AdminPagePermissions, PagePermissions
from cms.shared import checks
from cms.shared.checks import OperationBlocked, can
from cms.shared.operations import OperationContext, operation
from cms.signals import (
    PAGE_OPERATION_SIGNALS,
    PLACEHOLDER_OPERATION_SIGNALS,
    post_obj_operation,
    post_placeholder_operation,
    pre_obj_operation,
)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import override_placeholder_conf
from cms.utils.compat.warnings import RemovedInDjangoCMS70Warning
from cms.utils.urlutils import admin_reverse

SLUG_NOT_UNIQUE = "You cannot have two pages with the same slug"


class RegistryIsolationMixin:
    """Keeps checks and operations registered by a test out of the other tests."""

    def setUp(self):
        super().setUp()
        saved = {operation: dict(entries) for operation, entries in checks._extensions.items()}
        saved_operations = dict(operations._registry)

        def restore():
            checks._extensions.clear()
            checks._extensions.update(saved)
            operations._registry.clear()
            operations._registry.update(saved_operations)

        self.addCleanup(restore)


class CheckRegistryTest(RegistryIsolationMixin, CMSTestCase):
    def setUp(self):
        super().setUp()
        self.context = OperationContext(user=self.get_superuser())
        self.page = create_page("Page", "nav_playground.html", "en")

    def test_core_checks_come_first_and_permissions_lead(self):
        names = [entry.name for entry in checks.get_checks(operations.MOVE_PAGE)]
        self.assertEqual(names[0], "cms.pages.move_permission")
        self.assertIn("cms.pages.url_unique", names)

    def test_an_app_check_runs_after_the_core_checks(self):
        def locked(context, *, page, **kwargs):
            raise ValidationError("Page is locked")

        checks.register_check(operations.MOVE_PAGE, "tests.locked", locked, requires=["page"])

        self.assertEqual(checks.get_checks(operations.MOVE_PAGE)[-1].name, "tests.locked")
        with self.assertRaisesMessage(ValidationError, "Page is locked"):
            page_services.move_page(self.page, self.page, "right", context=self.context)

    def test_an_app_check_replaces_a_core_check_in_place(self):
        before = [entry.name for entry in checks.get_checks(operations.MOVE_PAGE)]
        checks.register_check(operations.MOVE_PAGE, "cms.pages.url_unique", lambda context, **kwargs: None)

        entries = checks.get_checks(operations.MOVE_PAGE)
        self.assertEqual([entry.name for entry in entries], before)
        self.assertEqual(entries[before.index("cms.pages.url_unique")].check.__name__, "<lambda>")

    def test_cms_config_registers_checks(self):
        def check(context, **kwargs):
            pass

        class Config:
            cms_checks = {operations.MOVE_PAGE: [("tests.config", check, ["page"])]}

        CMSCoreExtensions().configure_app(Config)

        entry = checks.get_checks(operations.MOVE_PAGE)[-1]
        self.assertEqual((entry.name, entry.check, entry.requires), ("tests.config", check, ("page",)))

    def test_cms_config_registers_a_check_kind(self):
        def check(context, **kwargs):
            pass

        class Config:
            cms_checks = {operations.MOVE_PAGE: [("tests.kind", check, ["page"], checks.PERMISSION)]}

        CMSCoreExtensions().configure_app(Config)

        entry = next(entry for entry in checks.get_checks(operations.MOVE_PAGE) if entry.name == "tests.kind")
        self.assertEqual(entry.kind, checks.PERMISSION)

    def test_checks_run_by_kind(self):
        def check(context, **kwargs):
            pass

        checks.register_check(operations.MOVE_PAGE, "tests.validation", check)
        checks.register_check(operations.MOVE_PAGE, "tests.policy", check, kind=checks.POLICY)
        checks.register_check(operations.MOVE_PAGE, "tests.permission", check, kind=checks.PERMISSION)

        entries = checks.get_checks(operations.MOVE_PAGE)
        kinds = [entry.kind for entry in entries]
        self.assertEqual(kinds, sorted(kinds, key=checks.KINDS.index))
        names = [entry.name for entry in entries]
        # Within a kind, the core checks come first.
        self.assertLess(names.index("cms.pages.move_target_permission"), names.index("tests.permission"))
        self.assertLess(names.index("tests.permission"), names.index("tests.policy"))
        self.assertLess(names.index("tests.policy"), names.index("cms.pages.url_unique"))
        self.assertLess(names.index("cms.pages.url_unique"), names.index("tests.validation"))

    def test_a_policy_check_blocks_the_operation(self):
        def published(context, **kwargs):
            raise OperationBlocked("Published content is read-only")

        checks.register_check(operations.MOVE_PAGE, "tests.published", published, kind=checks.POLICY)

        with self.assertRaisesMessage(OperationBlocked, "Published content is read-only"):
            page_services.move_page(self.page, self.page, "right", context=self.context)
        # Code handling PermissionDenied keeps refusing a blocked operation.
        self.assertTrue(issubclass(OperationBlocked, PermissionDenied))

    def test_dry_run_reports_policy_and_validation_separately(self):
        def published(context, **kwargs):
            raise OperationBlocked("Published")

        def invalid(context, **kwargs):
            raise ValidationError("Invalid")

        checks.register_check(operations.MOVE_PAGE, "tests.invalid", invalid)
        checks.register_check(operations.MOVE_PAGE, "tests.published", published, kind=checks.POLICY)

        verdict = can(operations.MOVE_PAGE, self.context, page=self.page, target_page=self.page, position="right")

        self.assertFalse(verdict)
        self.assertEqual(
            [(r.name, r.kind) for r in verdict.reasons],
            [("tests.published", checks.POLICY), ("tests.invalid", checks.VALIDATION)],
        )

    def test_a_system_context_runs_policy_checks_unless_it_opts_out(self):
        def published(context, **kwargs):
            raise OperationBlocked("Published")

        checks.register_check(operations.MOVE_PAGE, "tests.published", published, kind=checks.POLICY)
        target = {"page": self.page, "target_page": self.page, "position": "right"}

        with self.assertRaises(OperationBlocked):
            checks.run_checks(operations.MOVE_PAGE, OperationContext.system("tests"), **target)
        migration = OperationContext.system("tests.migration", policy=False)
        checks.run_checks(operations.MOVE_PAGE, migration, **target)
        self.assertTrue(can(operations.MOVE_PAGE, migration, **target))

    def test_only_a_system_context_skips_policy_checks(self):
        with self.assertRaises(ValueError):
            OperationContext(user=self.get_superuser(), policy=False)

    def test_cms_config_registers_a_policy_check(self):
        def check(context, **kwargs):
            pass

        class Config:
            cms_checks = {operations.MOVE_PAGE: [("tests.policy", check, (), "policy")]}

        CMSCoreExtensions().configure_app(Config)

        entry = next(entry for entry in checks.get_checks(operations.MOVE_PAGE) if entry.name == "tests.policy")
        self.assertEqual(entry.kind, checks.POLICY)

    def test_app_checks_default_to_validation(self):
        checks.register_check(operations.MOVE_PAGE, "tests.default", lambda context, **kwargs: None)
        self.assertEqual(checks.get_checks(operations.MOVE_PAGE)[-1].kind, checks.VALIDATION)

    def test_a_check_kind_is_validated(self):
        with self.assertRaises(ValueError):
            checks.register_check(operations.MOVE_PAGE, "tests.bad", lambda context, **kwargs: None, kind="other")
        with self.assertRaises(TypeError):
            # Core checks must say which kind they are.
            checks.register_core_check(operations.MOVE_PAGE, "tests.core", lambda context, **kwargs: None)

    def test_every_core_check_declares_its_kind(self):
        for entries in checks._core.values():
            for entry in entries.values():
                with self.subTest(check=entry.name):
                    self.assertIn(entry.kind, checks.KINDS)

    def test_a_system_context_skips_permission_checks_only(self):
        def refuse(context, **kwargs):
            raise PermissionDenied("Not you")

        def invalid(context, **kwargs):
            raise ValidationError("Never valid")

        checks.register_check(operations.MOVE_PAGE, "tests.refuse", refuse, kind=checks.PERMISSION)
        system = OperationContext.system("tests")
        target = {"page": self.page, "target_page": self.page, "position": "right"}

        checks.run_checks(operations.MOVE_PAGE, system, **target)  # the permission check is skipped
        self.assertTrue(can(operations.MOVE_PAGE, system, **target))
        staff = OperationContext(user=self._create_user("staff", is_staff=True))
        self.assertFalse(can(operations.MOVE_PAGE, staff, **target))

        checks.register_check(operations.MOVE_PAGE, "tests.invalid", invalid)
        with self.assertRaisesMessage(ValidationError, "Never valid"):
            checks.run_checks(operations.MOVE_PAGE, system, **target)
        verdict = can(operations.MOVE_PAGE, system, **target)
        self.assertEqual([r.name for r in verdict.reasons], ["tests.invalid"])
        self.assertTrue(verdict.complete)

    def test_a_system_context_names_its_caller(self):
        with self.assertRaises(ValueError):
            OperationContext.system("")
        context = OperationContext.system("tests", user=self.get_superuser())
        self.assertTrue(context.is_system)
        self.assertFalse(self.context.is_system)

    def test_dry_run_collects_every_validation_failure(self):
        def fail(message):
            def check(context, **kwargs):
                raise ValidationError(message)

            return check

        checks.register_check(operations.MOVE_PAGE, "tests.one", fail("One"))
        checks.register_check(operations.MOVE_PAGE, "tests.two", fail("Two"))

        verdict = can(operations.MOVE_PAGE, self.context, page=self.page, target_page=self.page, position="right")

        self.assertFalse(verdict)
        self.assertEqual([(r.name, r.kind) for r in verdict.reasons], [("tests.one", "validation"), ("tests.two", "validation")])
        self.assertEqual(str(verdict), "One Two")

    def test_dry_run_stops_at_a_permission_failure(self):
        def reveal(context, **kwargs):
            raise ValidationError("Something about the target")

        checks.register_check(operations.MOVE_PAGE, "tests.reveal", reveal)
        staff = self._create_user("staff", is_staff=True)

        verdict = can(
            operations.MOVE_PAGE,
            OperationContext(user=staff),
            page=self.page,
            target_page=self.page,
            position="right",
        )

        self.assertFalse(verdict)
        self.assertEqual([r.kind for r in verdict.reasons], ["permission"])

    def test_dry_run_without_a_target_is_incomplete(self):
        verdict = can(operations.MOVE_PAGE, self.context, page=self.page)

        self.assertTrue(verdict)
        self.assertFalse(verdict.complete)
        self.assertIn("cms.pages.url_unique", verdict.skipped)

    def test_a_real_run_requires_every_argument(self):
        with self.assertRaises(TypeError):
            checks.run_checks(operations.MOVE_PAGE, self.context, page=self.page)

    def test_dry_run_changes_nothing(self):
        other = create_page("Other", "nav_playground.html", "en")

        self.assertTrue(can(operations.MOVE_PAGE, self.context, page=self.page, target_page=other, position="first-child"))

        self.page.refresh_from_db()
        self.assertIsNone(self.page.parent_id)


class OperationFrameTest(RegistryIsolationMixin, CMSTestCase):
    def setUp(self):
        super().setUp()
        self.context = OperationContext(user=self.get_superuser())
        self.page = create_page("Page", "nav_playground.html", "en")
        self.sent = []
        for signal in PAGE_OPERATION_SIGNALS:
            signal.connect(self.receive)
            self.addCleanup(signal.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append((signal, kwargs))

    def frame(self, **kwargs):
        return operation(
            operations.MOVE_PAGE, self.context, signals=PAGE_OPERATION_SIGNALS, sender=Page, obj=self.page, **kwargs
        )

    def test_announces_the_operation_around_the_body(self):
        with self.frame() as signal_kwargs:
            self.assertEqual([signal for signal, _ in self.sent], [pre_obj_operation])
            signal_kwargs["obj"] = "after"

        self.assertEqual([signal for signal, _ in self.sent], [pre_obj_operation, post_obj_operation])
        (_, pre), (_, post) = self.sent
        self.assertEqual(pre["obj"], self.page)
        self.assertEqual(post["obj"], "after")
        self.assertEqual(pre["token"], post["token"])
        self.assertEqual(post["operation"], operations.MOVE_PAGE)

    def test_a_failing_check_announces_nothing(self):
        def refuse(context, **kwargs):
            raise ValidationError("No")

        checks.register_check(operations.MOVE_PAGE, "tests.refuse", refuse)

        with self.assertRaises(ValidationError):
            with self.frame(checks={"page": self.page, "target_page": self.page, "position": "right"}):
                self.fail("The body must not run")
        self.assertEqual(self.sent, [])

    def test_a_failing_body_sends_no_post_signal(self):
        with self.assertRaises(RuntimeError):
            with self.frame():
                raise RuntimeError
        self.assertEqual([signal for signal, _ in self.sent], [pre_obj_operation])

    def test_a_failing_post_receiver_undoes_the_operation(self):
        def fail(**kwargs):
            raise RuntimeError("receiver failed")

        post_obj_operation.connect(fail)
        self.addCleanup(post_obj_operation.disconnect, fail)
        target = create_page("Target", "nav_playground.html", "en")

        with self.assertRaisesMessage(RuntimeError, "receiver failed"):
            page_services.move_page(self.page, target, "first-child", context=self.context)

        self.page.refresh_from_db()
        self.assertIsNone(self.page.parent_id)

    def test_a_failing_receiver_undoes_a_plugin_operation(self):
        def fail(**kwargs):
            raise RuntimeError("receiver failed")

        placeholder = self.page.get_placeholders("en").get(slot="body")
        plugin = add_plugin(placeholder, "TextPlugin", "en", body="Text")
        post_placeholder_operation.connect(fail)
        self.addCleanup(post_placeholder_operation.disconnect, fail)

        with self.assertRaisesMessage(RuntimeError, "receiver failed"):
            plugin_services.delete_plugin(plugin.cmsplugin_ptr, context=self.context)

        self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_a_silenced_context_announces_nothing(self):
        self.context = OperationContext(user=self.get_superuser(), emit_signals=False)
        with self.frame():
            pass
        self.assertEqual(self.sent, [])


class OperationRegistryTest(RegistryIsolationMixin, CMSTestCase):
    def test_core_operations_are_declared(self):
        for operation_id in (
            operations.ADD_PLUGIN,
            operations.CHANGE_PLUGIN,
            operations.MOVE_PLUGIN,
            operations.CLEAR_PLACEHOLDER,
            operations.ADD_PAGE,
            operations.MOVE_PAGE,
            operations.CHANGE_USER_PERMISSIONS,
        ):
            with self.subTest(operation=operation_id):
                declaration = operations.get_operation(operation_id)
                self.assertEqual(declaration.id, operation_id)

    def test_every_declaration_has_a_summary_and_a_description(self):
        for declaration in operations.get_operations():
            with self.subTest(operation=declaration.id):
                self.assertTrue(str(declaration.summary))
                self.assertTrue(declaration.description)

    def test_the_summary_is_translatable(self):
        # Translated when shown, not when declared at import time.
        for declaration in operations.get_operations():
            with self.subTest(operation=declaration.id):
                self.assertIsInstance(declaration.summary, Promise)

    def test_every_operation_a_service_runs_is_declared(self):
        for operation_id in checks._core:
            with self.subTest(operation=operation_id):
                operations.get_operation(operation_id)

    def test_an_undeclared_operation_is_unknown(self):
        with self.assertRaises(LookupError):
            operations.get_operation("tests.unknown")
        with self.assertRaises(LookupError):
            with operation("tests.unknown", OperationContext(user=None)):
                self.fail("The body must not run")

    def test_an_operation_is_declared_once(self):
        with self.assertRaises(ValueError):
            operations.register_operation(operations.Operation(operations.MOVE_PAGE, summary="Again"))

    def test_the_description_defaults_to_the_service_docstring(self):
        def publish(article, *, context):
            """Publish an article."""

        declaration = operations.register_operation(
            operations.Operation("tests.publish", summary="Publish", service=publish)
        )

        self.assertEqual(declaration.description, "Publish an article.")
        self.assertEqual(operations.get_operation("tests.publish"), declaration)

    def test_cms_config_declares_operations(self):
        class Config:
            cms_operations = [operations.Operation("tests.publish", summary="Publish", description="Publish.")]

        CMSCoreExtensions().configure_app(Config)

        self.assertEqual(operations.get_operation("tests.publish").summary, "Publish")
        self.assertEqual(list(operations.get_operations())[-1].id, "tests.publish")

    def test_cms_config_refuses_bad_declarations(self):
        class NotAnOperation:
            cms_operations = [("tests.publish", "Publish")]

        class Duplicate:
            cms_operations = [operations.Operation(operations.MOVE_PAGE, summary="Move")]

        for config in (NotAnOperation, Duplicate):
            with self.subTest(config=config.__name__), self.assertRaises(ImproperlyConfigured):
                CMSCoreExtensions().configure_app(config)


class PluginServiceChecksTest(RegistryIsolationMixin, CMSTestCase):
    """The plugin services run the checks registered for their operation."""

    def setUp(self):
        super().setUp()
        self.context = OperationContext(user=self.get_superuser(), language="en")
        page = create_page("Page", "nav_playground.html", "en")
        placeholders = page.get_placeholders("en")
        self.body = placeholders.get(slot="body")
        self.other = placeholders.get(slot="right-column")
        self.plugin = add_plugin(self.body, "TextPlugin", "en", body="Text").cmsplugin_ptr
        add_plugin(self.body, "TextPlugin", "en", body="Second")
        self.clipboard = Placeholder.objects.create(slot="clipboard")
        UserSettings.objects.create(user=self.context.user, language="en", clipboard=self.clipboard)
        self.reference = plugin_services.copy_placeholder_to_clipboard(
            self.body, self.clipboard, "en", "en", context=self.context
        )
        self.sent = []
        for signal in PLACEHOLDER_OPERATION_SIGNALS:
            signal.connect(self.receive)
            self.addCleanup(signal.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append(kwargs["operation"])

    def calls(self):
        """Each service with an operation id, its call, and the arguments its checks receive."""
        return [
            (
                operations.MOVE_PLUGIN,
                lambda: plugin_services.move_plugin(self.plugin, 1, self.other, context=self.context),
                {"plugin": self.plugin, "target_position": 1, "target_placeholder": self.other, "target_parent": None},
            ),
            (
                operations.CUT_PLUGIN,
                lambda: plugin_services.cut_plugin(self.plugin, "en", self.clipboard, context=self.context),
                {"plugin": self.plugin, "target_language": "en", "target_placeholder": self.clipboard},
            ),
            (
                operations.PASTE_PLUGIN,
                lambda: plugin_services.paste_plugin(self.plugin, "en", self.other, 1, context=self.context),
                {
                    "plugin": self.plugin,
                    "target_language": "en",
                    "target_placeholder": self.other,
                    "target_position": 1,
                    "target_parent": None,
                },
            ),
            (
                operations.PASTE_PLACEHOLDER,
                lambda: plugin_services.paste_placeholder(self.reference, "en", self.other, 1, context=self.context),
                {"plugin": self.reference, "target_language": "en", "target_placeholder": self.other, "target_position": 1},
            ),
            (
                operations.ADD_PLUGINS_FROM_PLACEHOLDER,
                lambda: plugin_services.add_plugins_from_placeholder(
                    self.body, self.other, "en", "en", context=self.context
                ),
                {"source_placeholder": self.body, "target_placeholder": self.other, "source_language": "en", "target_language": "en"},
            ),
            (
                operations.DELETE_PLUGIN,
                lambda: plugin_services.delete_plugin(self.plugin, context=self.context),
                {"plugin": self.plugin},
            ),
            (
                operations.CLEAR_PLACEHOLDER,
                lambda: plugin_services.clear_placeholder(self.body, "en", context=self.context),
                {"placeholder": self.body, "language": "en"},
            ),
        ]

    def snapshot(self):
        return list(
            CMSPlugin.objects.order_by("pk").values_list("pk", "placeholder_id", "language", "parent_id", "position")
        )

    def test_a_blocking_check_stops_the_service_before_anything_happens(self):
        for operation_id, call, arguments in self.calls():
            with self.subTest(operation=operation_id):
                received = []

                def published(context, received=received, **kwargs):
                    received.append(kwargs)
                    raise OperationBlocked("Published content is read-only")

                checks.register_check(operation_id, "tests.published", published, kind=checks.POLICY)
                self.addCleanup(checks._extensions[operation_id].pop, "tests.published")
                before = self.snapshot()

                with self.assertRaisesMessage(OperationBlocked, "Published content is read-only"):
                    call()

                self.assertEqual(self.sent, [])
                self.assertEqual(self.snapshot(), before)
                (kwargs,) = received
                self.assertEqual({key: kwargs[key] for key in arguments}, arguments)
                self.assertIn("permissions", kwargs)
                # The dry run with the same arguments agrees.
                verdict = can(operation_id, self.context, **arguments)
                self.assertEqual([(r.name, r.kind) for r in verdict.reasons], [("tests.published", checks.POLICY)])

    def test_a_passing_check_lets_the_service_run(self):
        checks.register_check(operations.MOVE_PLUGIN, "tests.allowed", lambda context, **kwargs: None)

        plugin_services.move_plugin(self.plugin, 1, self.other, context=self.context)

        self.assertEqual(self.sent, [operations.MOVE_PLUGIN, operations.MOVE_PLUGIN])
        self.assertEqual(CMSPlugin.objects.get(pk=self.plugin.pk).placeholder_id, self.other.pk)


class CorePluginChecksTest(RegistryIsolationMixin, CMSTestCase):
    """The core checks of the plugin operations, seen by the services and by ``can()``."""

    def setUp(self):
        super().setUp()
        self.superuser = self.get_superuser()
        self.context = OperationContext(user=self.superuser, language="en")
        page = create_page("Page", "nav_playground.html", "en")
        placeholders = page.get_placeholders("en")
        self.body = placeholders.get(slot="body")
        self.other = placeholders.get(slot="right-column")
        self.plugin = add_plugin(self.body, "TextPlugin", "en", body="Text").cmsplugin_ptr
        self.sent = []
        for signal in PLACEHOLDER_OPERATION_SIGNALS:
            signal.connect(self.receive)
            self.addCleanup(signal.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append(kwargs["operation"])

    def only_in_body(self):
        return patch.object(plugin_pool.get_plugin("TextPlugin"), "allowed_slots", ["body"])

    def test_every_plugin_operation_has_permission_and_policy_checks(self):
        for operation_id in (
            operations.MOVE_PLUGIN,
            operations.CUT_PLUGIN,
            operations.PASTE_PLUGIN,
            operations.PASTE_PLACEHOLDER,
            operations.COPY_PLUGIN_TO_CLIPBOARD,
            operations.COPY_PLACEHOLDER_TO_CLIPBOARD,
            operations.ADD_PLUGINS_FROM_PLACEHOLDER,
            operations.DELETE_PLUGIN,
            operations.CLEAR_PLACEHOLDER,
        ):
            with self.subTest(operation=operation_id):
                operations.get_operation(operation_id)
                kinds = {entry.kind for entry in checks.get_checks(operation_id) if entry.name.startswith("cms.core.")}
                self.assertLessEqual({checks.PERMISSION, checks.POLICY}, kinds)

    def test_the_dry_run_sees_the_core_permission_check(self):
        staff = OperationContext(user=self.get_staff_user_with_no_permissions(), language="en")

        verdict = can(operations.MOVE_PLUGIN, staff, plugin=self.plugin, target_placeholder=self.other)

        self.assertEqual([(r.name, r.kind) for r in verdict.reasons], [("cms.core.move_permission", checks.PERMISSION)])
        with self.assertRaises(PermissionDenied) as raised:
            plugin_services.move_plugin(self.plugin, 1, self.other, context=staff)
        self.assertNotIsInstance(raised.exception, OperationBlocked)
        self.assertEqual(self.sent, [])

    def test_content_that_cannot_be_edited_blocks_the_operation(self):
        with patch.object(Placeholder, "check_source", return_value=False):
            verdict = can(operations.DELETE_PLUGIN, self.context, plugin=self.plugin)
            with self.assertRaises(OperationBlocked):
                plugin_services.delete_plugin(self.plugin, context=self.context)

        self.assertEqual([(r.name, r.kind) for r in verdict.reasons], [("cms.core.source_editable", checks.POLICY)])
        self.assertEqual(self.sent, [])
        self.assertTrue(CMSPlugin.objects.filter(pk=self.plugin.pk).exists())

    def test_a_system_context_skips_permissions_but_not_policy(self):
        system = OperationContext.system("tests")

        with patch.object(Placeholder, "check_source", return_value=False):
            with self.assertRaises(OperationBlocked):
                plugin_services.clear_placeholder(self.body, "en", context=system)
            plugin_services.clear_placeholder(
                self.body, "en", context=OperationContext.system("tests.migration", policy=False)
            )

        self.assertFalse(self.body.get_plugins("en").exists())

    def test_a_system_context_can_move_without_a_user(self):
        moved = plugin_services.move_plugin(self.plugin, 1, self.other, context=OperationContext.system("tests"))

        self.assertEqual(moved.placeholder_id, self.other.pk)

    def test_moving_into_a_slot_the_plugin_is_not_allowed_in_is_refused(self):
        with self.only_in_body():
            verdict = can(operations.MOVE_PLUGIN, self.context, plugin=self.plugin, target_placeholder=self.other)
            with self.assertRaisesMessage(ValidationError, "is not allowed in placeholder 'right-column'"):
                plugin_services.move_plugin(self.plugin, 1, self.other, context=self.context)
            # Moving within the placeholder is not affected.
            plugin_services.move_plugin(self.plugin, 1, context=self.context)

        self.assertEqual([(r.name, r.kind) for r in verdict.reasons], [("cms.core.allowed_in_slot", checks.VALIDATION)])
        self.assertEqual(CMSPlugin.objects.get(pk=self.plugin.pk).placeholder_id, self.body.pk)

    def test_copying_into_a_slot_checks_every_copied_plugin(self):
        clipboard = Placeholder.objects.create(slot="clipboard")
        UserSettings.objects.create(user=self.superuser, language="en", clipboard=clipboard)
        reference = plugin_services.copy_placeholder_to_clipboard(
            self.body, clipboard, "en", "en", context=self.context
        )

        with self.only_in_body():
            with self.assertRaises(ValidationError):
                plugin_services.paste_placeholder(reference, "en", self.other, 1, context=self.context)
            with self.assertRaises(ValidationError):
                plugin_services.add_plugins_from_placeholder(self.body, self.other, "en", "en", context=self.context)
            # The clipboard takes any plugin.
            plugin_services.cut_plugin(self.plugin, "en", clipboard, context=self.context)

        self.assertFalse(self.other.get_plugins("en").exists())

    def test_the_admin_answers_a_disallowed_slot_with_400(self):
        clipboard = Placeholder.objects.create(slot="clipboard")
        UserSettings.objects.create(user=self.superuser, language="en", clipboard=clipboard)
        reference = plugin_services.copy_placeholder_to_clipboard(
            self.body, clipboard, "en", "en", context=self.context
        )
        moves = {
            "move": {"plugin_id": self.plugin.pk, "placeholder_id": self.other.pk},
            "paste placeholder": {"plugin_id": reference.pk, "placeholder_id": self.other.pk, "move_a_copy": "true"},
        }

        with self.only_in_body(), self.login_user_context(self.superuser):
            for label, data in moves.items():
                with self.subTest(label):
                    response = self.client.post(
                        self.get_move_plugin_uri(self.plugin),
                        {**data, "target_language": "en", "target_position": 1},
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("not allowed in placeholder", response.content.decode())

        self.assertFalse(self.other.get_plugins("en").exists())


class PluginDataServicesTest(RegistryIsolationMixin, CMSTestCase):
    """``add_plugin`` and ``change_plugin``: data in, cleaned by the plugin's form."""

    def setUp(self):
        super().setUp()
        self.context = OperationContext(user=self.get_superuser(), language="en")
        page = create_page("Page", "nav_playground.html", "en")
        placeholders = page.get_placeholders("en")
        self.body = placeholders.get(slot="body")
        self.other = placeholders.get(slot="right-column")
        self.sent = []
        for signal in PLACEHOLDER_OPERATION_SIGNALS:
            signal.connect(self.receive)
            self.addCleanup(signal.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append((signal, kwargs))

    def add_link(self, **kwargs):
        data = kwargs.pop("data", {"name": "  A link  ", "external_link": "https://www.django-cms.org"})
        return plugin_services.add_plugin(self.body, "LinkPlugin", "en", data, context=self.context, **kwargs)

    def test_add_cleans_the_data_through_the_plugin_form(self):
        plugin = self.add_link()

        plugin.refresh_from_db()
        self.assertEqual(plugin.name, "A link")  # stripped by the form field
        self.assertEqual((plugin.placeholder_id, plugin.language, plugin.plugin_type), (self.body.pk, "en", "LinkPlugin"))
        (pre_signal, pre), (post_signal, post) = self.sent
        self.assertEqual((pre_signal, post_signal), PLACEHOLDER_OPERATION_SIGNALS)
        self.assertEqual(post["operation"], operations.ADD_PLUGIN)
        self.assertEqual(pre["token"], post["token"])
        self.assertEqual((post["plugin"], post["placeholder"]), (plugin, self.body))
        self.assertEqual(post["tree_order"], [plugin.pk])

    def test_invalid_data_is_refused_before_anything_happens(self):
        with self.assertRaises(ValidationError) as raised:
            self.add_link(data={"name": "A link", "external_link": "not a url"})

        self.assertIn("external_link", raised.exception.message_dict)
        self.assertEqual(self.sent, [])
        self.assertFalse(self.body.get_plugins("en").exists())

    def test_tree_fields_cannot_be_set_through_data(self):
        plugin = self.add_link(
            data={"name": "A link", "external_link": "https://www.django-cms.org", "placeholder": self.other.pk, "position": 99}
        )

        self.assertEqual((plugin.placeholder_id, plugin.position), (self.body.pk, 1))

    def test_positions(self):
        first = self.add_link()
        child = self.add_link(target=first, position="last-child")
        before = self.add_link(target=first, position="left")
        top = self.add_link(position="first-child")

        tree = [(p.pk, p.parent_id) for p in self.body.get_plugins("en").order_by("position")]
        self.assertEqual(tree, [(top.pk, None), (before.pk, None), (first.pk, None), (child.pk, first.pk)])

    def test_a_plugin_can_replace_the_data_cleaning(self):
        LinkPlugin = plugin_pool.get_plugin("LinkPlugin")
        original = LinkPlugin.clean_plugin_data.__func__

        def clean_plugin_data(cls, obj, data, *, instance=None):
            return original(cls, obj, {**data, "name": data["name"].upper()}, instance=instance)

        with patch.object(LinkPlugin, "clean_plugin_data", classmethod(clean_plugin_data)):
            plugin = self.add_link()

        self.assertEqual(plugin.name, "A LINK")

    def test_change_only_needs_the_fields_that_change(self):
        plugin = self.add_link()
        self.sent.clear()

        changed = plugin_services.change_plugin(plugin.cmsplugin_ptr, {"name": "Renamed"}, context=self.context)

        changed.refresh_from_db()
        self.assertEqual((changed.name, changed.external_link), ("Renamed", "https://www.django-cms.org"))
        (_, pre), (_, post) = self.sent
        self.assertEqual(post["operation"], operations.CHANGE_PLUGIN)
        self.assertEqual((pre["old_plugin"].name, post["new_plugin"].name), ("A link", "Renamed"))
        with self.assertRaises(ValidationError):
            plugin_services.change_plugin(changed, {"external_link": "not a url"}, context=self.context)

    def test_add_and_change_run_their_checks(self):
        staff = OperationContext(user=self.get_staff_user_with_no_permissions(), language="en")
        plugin = self.add_link()

        verdict = can(operations.ADD_PLUGIN, staff, placeholder=self.body, plugin_type="LinkPlugin", language="en")
        self.assertEqual([r.name for r in verdict.reasons], ["cms.core.add_permission"])
        with self.assertRaises(PermissionDenied):
            plugin_services.change_plugin(plugin, {"name": "No"}, context=staff)
        with patch.object(Placeholder, "check_source", return_value=False), self.assertRaises(OperationBlocked):
            self.add_link()

    def test_add_validates_the_destination(self):
        foreign = plugin_services.add_plugin(
            self.other, "LinkPlugin", "en", {"name": "B", "external_link": "https://b.org"}, context=self.context
        )
        cases = {
            "unknown type": dict(plugin_type="NoSuchPlugin"),
            "parent elsewhere": dict(target=foreign),
        }
        for label, kwargs in cases.items():
            with self.subTest(label), self.assertRaises(ValidationError):
                plugin_services.add_plugin(
                    self.body,
                    kwargs.pop("plugin_type", "LinkPlugin"),
                    "en",
                    {"name": "A", "external_link": "https://a.org"},
                    context=self.context,
                    **kwargs,
                )
        with self.only_in("right-column"), self.assertRaises(ValidationError):
            self.add_link()
        with override_placeholder_conf(CMS_PLACEHOLDER_CONF={"body": {"limits": {"LinkPlugin": 1}}}):
            self.add_link()
            with self.assertRaises(ValidationError):
                self.add_link()

    def only_in(self, slot):
        return patch.object(plugin_pool.get_plugin("LinkPlugin"), "allowed_slots", [slot])

    def test_a_system_context_adds_without_a_user(self):
        plugin = plugin_services.add_plugin(
            self.body,
            "LinkPlugin",
            "en",
            {"name": "A link", "external_link": "https://www.django-cms.org"},
            context=OperationContext.system("tests"),
        )

        self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_the_admin_saves_through_the_service(self):
        uri = self.get_add_plugin_uri(placeholder=self.body, plugin_type="LinkPlugin", language="en")

        with patch("django.contrib.admin.site._registry", {}), self.login_user_context(self.get_superuser()):
            # save_model must not need the placeholder admin from the admin site.
            response = self.client.post(uri, {"name": "A link", "external_link": "https://www.django-cms.org"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([kwargs["operation"] for _, kwargs in self.sent], [operations.ADD_PLUGIN] * 2)
        self.assertEqual(self.body.get_plugins("en").count(), 1)


class PluginTreeRulesTest(RegistryIsolationMixin, CMSTestCase):
    """Which plugin may go where: parent and child classes, and the site's languages."""

    def setUp(self):
        super().setUp()
        self.context = OperationContext(user=self.get_superuser(), language="en")
        page = create_page("Page", "nav_playground.html", "en")
        placeholders = page.get_placeholders("en")
        self.body = placeholders.get(slot="body")
        self.other = placeholders.get(slot="right-column")
        self.columns = add_plugin(self.body, "MultiColumnPlugin", "en")

    def add(self, plugin_type, **kwargs):
        return plugin_services.add_plugin(
            kwargs.pop("placeholder", self.body), plugin_type, kwargs.pop("language", "en"), context=self.context,
            **kwargs,
        )

    def test_add_follows_the_parent_and_child_classes(self):
        # MultiColumnPlugin only takes ColumnPlugin children; ColumnPlugin needs it as parent.
        column = self.add("ColumnPlugin", target=self.columns)
        with self.assertRaisesMessage(ValidationError, "not allowed inside MultiColumnPlugin"):
            self.add("TextPlugin", data={"body": "Text"}, target=self.columns)
        with self.assertRaisesMessage(ValidationError, "can only be added inside another plugin"):
            self.add("ColumnPlugin")

        verdict = can(operations.ADD_PLUGIN, self.context, placeholder=self.body, plugin_type="ColumnPlugin", language="en")
        self.assertEqual([r.name for r in verdict.reasons], ["cms.core.parent_allowed"])
        self.assertEqual(self.body.get_plugins("en").count(), 2)
        self.assertEqual(column.parent_id, self.columns.pk)

    def test_text_takes_its_inline_plugins(self):
        # djangocms-text hides its children from the structure board (allow_children
        # is off), but text-enabled plugins are still allowed inside it.
        text = add_plugin(self.body, "TextPlugin", "en", body="Text")

        link = self.add(
            "LinkPlugin", data={"name": "A link", "external_link": "https://www.django-cms.org"}, target=text
        )

        self.assertEqual(link.parent_id, text.pk)

    def test_move_and_paste_follow_the_parent_and_child_classes(self):
        text = add_plugin(self.other, "TextPlugin", "en", body="Text")

        with self.assertRaisesMessage(ValidationError, "not allowed inside MultiColumnPlugin"):
            plugin_services.move_plugin(text, 2, self.body, target_parent=self.columns, context=self.context)
        with self.assertRaisesMessage(ValidationError, "not allowed inside MultiColumnPlugin"):
            plugin_services.paste_plugin(text, "en", self.body, 2, target_parent=self.columns, context=self.context)

    def test_reordering_keeps_an_existing_tree_movable(self):
        # A tree that breaks the rules (created before they were checked, or by
        # code that does not check) can still be reordered under the same parent.
        invalid = add_plugin(self.body, "TextPlugin", "en", body="Text", target=self.columns)
        add_plugin(self.body, "TextPlugin", "en", body="Second", target=self.columns)

        plugin_services.move_plugin(invalid, 3, target_parent=self.columns, context=self.context)

        self.assertEqual(CMSPlugin.objects.get(pk=invalid.pk).parent_id, self.columns.pk)

    def test_the_language_belongs_to_the_site(self):
        with self.assertRaisesMessage(ValidationError, "supported language"):
            self.add("LinkPlugin", data={"name": "A", "external_link": "https://a.org"}, language="xx")
        with self.assertRaisesMessage(ValidationError, "supported language"):
            plugin_services.add_plugins_from_placeholder(self.body, self.other, "en", "xx", context=self.context)

        self.add("LinkPlugin", data={"name": "A", "external_link": "https://a.org"}, language="de")


class PlaceholderAdminAdapterTest(RegistryIsolationMixin, CMSTestCase):
    """The placeholder admin translates the services' refusals into HTTP answers."""

    def setUp(self):
        super().setUp()
        self.superuser = self.get_superuser()
        page = create_page("Page", "nav_playground.html", "en")
        placeholders = page.get_placeholders("en")
        self.body = placeholders.get(slot="body")
        self.other = placeholders.get(slot="right-column")
        self.plugin = add_plugin(self.body, "TextPlugin", "en", body="Text").cmsplugin_ptr
        self.sent = []
        for signal in PLACEHOLDER_OPERATION_SIGNALS:
            signal.connect(self.receive)
            self.addCleanup(signal.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append(kwargs)

    def move(self, user=None, uri=None, **data):
        with self.login_user_context(user or self.superuser):
            return self.client.post(
                uri or self.get_move_plugin_uri(self.plugin),
                {"plugin_id": self.plugin.pk, "target_language": "en", "target_position": 1, **data},
            )

    def test_refusals_are_answered_by_kind(self):
        with patch.object(Placeholder, "check_source", return_value=False):
            blocked = self.move(placeholder_id=self.other.pk)
        refused = self.move(user=self.get_staff_user_with_no_permissions(), placeholder_id=self.other.pk)
        with patch.object(plugin_pool.get_plugin("TextPlugin"), "allowed_slots", ["body"]):
            invalid = self.move(placeholder_id=self.other.pk)

        self.assertEqual((blocked.status_code, blocked.content.decode()), (409, str(core_checks.NOT_EDITABLE)))
        self.assertEqual((refused.status_code, refused.content.decode()), (403, str(core_checks.MOVE_DENIED)))
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.sent, [])
        self.assertEqual(CMSPlugin.objects.get(pk=self.plugin.pk).placeholder_id, self.body.pk)

    def test_the_services_decide_moves_into_the_plugin_tree(self):
        child = add_plugin(self.body, "TextPlugin", "en", body="Child", target=self.plugin)

        response = self.move(plugin_parent=child.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot be moved inside itself", response.content.decode())

    def test_the_plugin_limit_applies_to_moves_and_pastes(self):
        add_plugin(self.other, "TextPlugin", "en", body="Already there")

        with override_placeholder_conf(CMS_PLACEHOLDER_CONF={"right-column": {"limits": {"TextPlugin": 1}}}):
            moved = self.move(placeholder_id=self.other.pk)
            pasted = self.move(placeholder_id=self.other.pk, move_a_copy="true")

        self.assertEqual((moved.status_code, pasted.status_code), (400, 400))
        self.assertEqual(self.other.get_plugins("en").count(), 1)

    def test_an_endpoint_without_cms_path_announces_the_operation(self):
        response = self.move(uri=admin_reverse("cms_placeholder_move_plugin"), placeholder_id=self.other.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([kwargs["operation"] for kwargs in self.sent], [operations.MOVE_PLUGIN] * 2)
        self.assertIsNone(self.sent[0]["origin"])

    def test_deleting_and_editing_are_decided_by_the_services(self):
        staff = self.get_staff_user_with_no_permissions()
        with self.login_user_context(staff):
            deleted = self.client.post(self.get_delete_plugin_uri(self.plugin), {"post": "yes"})
        with patch.object(Placeholder, "check_source", return_value=False), self.login_user_context(self.superuser):
            edited = self.client.post(self.get_change_plugin_uri(self.plugin), {"body": "Changed"})

        self.assertEqual(deleted.status_code, 403)
        self.assertEqual(edited.status_code, 409)
        self.assertTrue(CMSPlugin.objects.filter(pk=self.plugin.pk).exists())

    def test_overriding_a_private_helper_is_deprecated(self):
        from cms.core.admin.placeholder import PlaceholderAdmin

        with self.assertWarns(RemovedInDjangoCMS70Warning):
            type("CustomPlaceholderAdmin", (PlaceholderAdmin,), {"_move_plugin": lambda self, *args, **kwargs: None})
        with self.assertWarns(RemovedInDjangoCMS70Warning):
            type("TemplatePlaceholderAdmin", (PlaceholderAdmin,), {"get_placeholder_template": lambda *args: None})


class MovePageChecksTest(CMSTestCase):
    """The ``MOVE_PAGE`` core checks, reached the way the page tree reaches them."""

    def setUp(self):
        super().setUp()
        self.site = Site.objects.get(pk=1)
        self.context = OperationContext(user=self.get_superuser())

    def tree_options(self, page, target, position, site=None):
        form = MovePageForm(data={"target": target, "position": position}, page=page, site=site or self.site)
        self.assertTrue(form.is_valid(), form.errors)
        return form.get_tree_options()

    def can_move(self, page, target, position, site=None):
        target_page, tree_position = self.tree_options(page, target, position, site)
        return can(operations.MOVE_PAGE, self.context, page=page, target_page=target_page, position=tree_position)

    def move(self, page, target, position, site=None):
        page_services.move_page(page, *self.tree_options(page, target, position, site), context=self.context)
        page.refresh_from_db()

    def assertSlugNotUnique(self, verdict):
        self.assertFalse(verdict)
        self.assertIn(SLUG_NOT_UNIQUE, str(verdict))

    def test_move_between_parents(self):
        parent1 = create_page("Parent 1", "nav_playground.html", "en")
        parent2 = create_page("Parent 2", "nav_playground.html", "en")
        child1 = create_page("Child 1", "nav_playground.html", "en", parent=parent1)
        self.assertTrue(self.can_move(child1, parent2.pk, 0))

        child2 = create_page("Child 2", "nav_playground.html", "en", parent=parent2)
        self.assertTrue(self.can_move(child2, parent1.pk, 0))

        # Same slug as child1
        child3 = create_page("Child 1", "nav_playground.html", "en", parent=parent2)
        self.assertSlugNotUnique(self.can_move(child3, parent1.pk, 0))

    def test_home_page_stays_a_root_page(self):
        parent = create_page("Parent", "nav_playground.html", "en")
        home = create_page("Home", "nav_playground.html", "en")
        home.set_as_homepage()

        verdict = self.can_move(home, parent.pk, 0)

        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.home_stays_root")
        self.assertIn("You can't move the home page inside another page", str(verdict))

    def test_move_without_urls(self):
        target = create_page("Target", "nav_playground.html", "en")
        page = create_page("Unpublished", "nav_playground.html", "en")
        # A never-published page can have content but no public URL yet.
        page.urls.all().delete()

        for destination in ("", target.pk):
            with self.subTest(target=destination):
                self.move(page, destination, 0)
                self.assertEqual(page.parent_id, destination or None)
                self.assertFalse(page.urls.exists())

    def test_checks_all_url_languages(self):
        source = create_page("Source", "nav_playground.html", "en")
        target = create_page("Target", "nav_playground.html", "en")
        create_page_content("de", "Ziel", target, slug="ziel")
        page = create_page("Child", "nav_playground.html", "en", parent=source)
        create_page_content("de", "Kind", page, slug="kind")
        create_page("Kind", "nav_playground.html", "de", parent=target, slug="kind")

        with force_language("en"):
            self.assertSlugNotUnique(self.can_move(page, target.pk, 0))

    def test_keeps_overwritten_urls(self):
        source = create_page("Source", "nav_playground.html", "en")
        target = create_page("Target", "nav_playground.html", "en")
        create_page_content("de", "Ziel", target, slug="ziel")
        page = create_page("Child", "nav_playground.html", "en", parent=source)
        create_page_content("de", "Kind", page, slug="kind", overwrite_url="custom")
        # Would collide with the synthesized path "ziel/kind", but the
        # overwritten German URL stays at "custom" after the move.
        create_page("Kind", "nav_playground.html", "de", parent=target, slug="kind")

        with force_language("en"):
            self.move(page, target.pk, 0)

        self.assertEqual(page.parent_id, target.pk)
        self.assertEqual(page.get_path("de"), "custom")

    def test_keeps_overwritten_urls_next_to_sibling(self):
        source = create_page("Source", "nav_playground.html", "en")
        target = create_page("Target", "nav_playground.html", "en")
        create_page_content("de", "Ziel", target, slug="ziel")
        page = create_page("Child", "nav_playground.html", "en", parent=source)
        create_page_content("de", "Kind", page, slug="kind", overwrite_url="custom")
        create_page("Other", "nav_playground.html", "en", parent=target)
        # A sibling with the same German slug does not collide with the
        # overwritten German URL, whatever the insert position.
        create_page("Kind", "nav_playground.html", "de", parent=target, slug="kind")

        with force_language("en"):
            self.move(page, target.pk, 1)

        self.assertEqual(page.parent_id, target.pk)
        self.assertEqual(page.get_path("de"), "custom")

    def test_reorders_home_page(self):
        home = create_page("Home", "nav_playground.html", "en")
        create_page_content("de", "Start", home, slug="start")
        home.set_as_homepage()
        other = create_page("Other", "nav_playground.html", "en")
        # Matches the German slug of the home page, whose URLs never change
        # when it is reordered among the root pages.
        create_page_content("de", "Andere", other, slug="andere", overwrite_url="start")

        with force_language("en"):
            self.move(home, "", 1)

        self.assertTrue(home.is_home)
        self.assertEqual(home.get_path("de"), "")

    def test_below_unreachable_parent(self):
        target = create_page("Target", "nav_playground.html", "en")
        create_page_content("de", "Ziel", target, slug="ziel")
        # The German translation of the target has no public path.
        target.urls.filter(language="de").update(path=None)
        source = create_page("Source", "nav_playground.html", "en")
        create_page_content("de", "Quelle", source, slug="quelle")
        page = create_page("Child", "nav_playground.html", "en", parent=source)
        create_page_content("de", "Kind", page, slug="kind")
        # Would collide if the page were checked as a root page, but below an
        # unreachable parent its German URL stays unreachable.
        create_page("Kind", "nav_playground.html", "de", slug="kind")

        with force_language("en"):
            self.move(page, target.pk, 0)

        self.assertEqual(page.parent_id, target.pk)
        self.assertIsNone(page.get_path("de"))

    def test_sibling_slug_collision(self):
        parent1 = create_page("Parent 1", "nav_playground.html", "en", slug="parent-1")
        parent2 = create_page("Parent 2", "nav_playground.html", "en", slug="parent-2")
        create_page("Test Page", "nav_playground.html", "en", slug="test", parent=parent1)
        # Allowed: different parents
        child2 = create_page("Test Page", "nav_playground.html", "en", slug="test", parent=parent2)

        self.assertSlugNotUnique(self.can_move(child2, parent1.pk, 2))

    def test_root_page_ignores_other_sites(self):
        """Moving a root page must only check its siblings on the page's own site (#8830)"""
        site2 = Site.objects.create(pk=2, domain="site2.com", name="site2")

        # Identical root level trees on both sites, as produced by ``manage.py cms copy-site``
        for site in (self.site, site2):
            create_page("A", "nav_playground.html", "de", slug="a", site=site)
            create_page("B", "nav_playground.html", "de", slug="b", site=site)

        page_b = Page.objects.filter(site=site2, urls__slug="b", urls__language="de").distinct().get()

        with force_language("de"):
            self.assertTrue(self.can_move(page_b, "", 0, site=site2))

    def test_child_parent_slug_collision(self):
        grandparent = create_page("Grandparent", "nav_playground.html", "en", slug="grandparent")
        parent = create_page("Parent", "nav_playground.html", "en", slug="parent", parent=grandparent)
        child = create_page("Child", "nav_playground.html", "en", slug="parent", parent=parent)

        self.assertSlugNotUnique(self.can_move(child, grandparent.pk, 2))

    def test_invalid_parent_path_is_not_reported_as_a_slug_conflict(self):
        target = create_page("Target", "nav_playground.html", "en")
        # A path stored before paths were validated.
        target.urls.filter(language="en").update(path="tar<get>")
        page = create_page("Child", "nav_playground.html", "en")

        verdict = self.can_move(page, target.pk, 0)

        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.url_unique")
        self.assertIn("Enter a valid", str(verdict))
        self.assertNotIn(SLUG_NOT_UNIQUE, str(verdict))

    def test_service_raises_what_the_dry_run_reports(self):
        parent1 = create_page("Parent 1", "nav_playground.html", "en")
        parent2 = create_page("Parent 2", "nav_playground.html", "en")
        create_page("Child", "nav_playground.html", "en", parent=parent1)
        page = create_page("Child", "nav_playground.html", "en", parent=parent2)

        with self.assertRaisesMessage(ValidationError, SLUG_NOT_UNIQUE):
            self.move(page, parent1.pk, 0)

    def test_permission_is_checked_before_the_urls(self):
        parent1 = create_page("Parent 1", "nav_playground.html", "en")
        parent2 = create_page("Parent 2", "nav_playground.html", "en")
        create_page("Child", "nav_playground.html", "en", parent=parent1)
        page = create_page("Child", "nav_playground.html", "en", parent=parent2)
        self.context = OperationContext(user=self._create_user("staff", is_staff=True))

        with self.assertRaises(PermissionDenied):
            self.move(page, parent1.pk, 0)

    def test_target_permission_is_checked_on_the_new_parent(self):
        parent = create_page("Parent", "nav_playground.html", "en")
        sibling = create_page("Sibling", "nav_playground.html", "en", parent=parent)
        page = create_page("Page", "nav_playground.html", "en")
        asked = []

        class Recording(PagePermissions):
            def can_add_subpage(self, target, site):
                asked.append(target)
                return target == parent

        verdict = can(
            operations.MOVE_PAGE,
            self.context,
            page=page,
            target_page=sibling,
            position="right",
            permissions=Recording(self.context.user),
        )

        self.assertTrue(verdict, str(verdict))
        self.assertEqual(asked, [parent])

    def test_moving_to_the_root_needs_no_subpage_permission(self):
        root = create_page("Root", "nav_playground.html", "en")
        parent = create_page("Parent", "nav_playground.html", "en")
        page = create_page("Page", "nav_playground.html", "en", parent=parent)

        class NoSubpages(PagePermissions):
            def can_add_subpage(self, target, site):
                return False

        verdict = can(
            operations.MOVE_PAGE,
            self.context,
            page=page,
            target_page=root,
            position="right",
            permissions=NoSubpages(self.context.user),
        )

        self.assertTrue(verdict, str(verdict))


class PageOperationChecksTest(CMSTestCase):
    """The core checks of the page operations other than moving."""

    def setUp(self):
        super().setUp()
        self.site = Site.objects.get(pk=1)
        self.context = OperationContext(user=self.get_superuser())
        self.sent = []
        post_obj_operation.connect(self.receive)
        self.addCleanup(post_obj_operation.disconnect, self.receive)

    def receive(self, signal, **kwargs):
        self.sent.append(kwargs)

    def test_set_home_refuses_a_page_that_is_not_a_root(self):
        parent = create_page("Parent", "nav_playground.html", "en")
        child = create_page("Child", "nav_playground.html", "en", parent=parent)

        verdict = can(operations.SET_HOME, self.context, page=child)
        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.home_candidate")
        with self.assertRaises(ValidationError):
            page_services.set_home(child, context=self.context)

    def test_set_home_is_announced(self):
        page = create_page("Page", "nav_playground.html", "en")

        page_services.set_home(page, context=self.context)

        page.refresh_from_db()
        self.assertTrue(page.is_home)
        self.assertEqual([(kw["operation"], kw["obj"]) for kw in self.sent], [(operations.SET_HOME, page)])

    def test_copy_checks_the_new_parent_not_the_sibling(self):
        parent = create_page("Parent", "nav_playground.html", "en")
        sibling = create_page("Sibling", "nav_playground.html", "en", parent=parent)
        page = create_page("Page", "nav_playground.html", "en")
        asked = []

        class Recording(PagePermissions):
            def can_add_subpage(self, target, site):
                asked.append(target)
                return target == parent

        verdict = can(
            operations.COPY_PAGE,
            self.context,
            page=page,
            target_page=sibling,
            position="right",
            target_site=self.site,
            permissions=Recording(self.context.user),
        )

        self.assertTrue(verdict, str(verdict))
        self.assertEqual(asked, [parent])

    def test_copy_refuses_a_page_without_a_language_of_the_target_site(self):
        site2 = Site.objects.create(pk=2, domain="site2.com", name="site2")
        page = create_page("Page", "nav_playground.html", "en")

        with self.settings(CMS_LANGUAGES={2: [{"code": "de", "name": "German"}]}):
            verdict = can(
                operations.COPY_PAGE, self.context, page=page, target_page=None, position="last-child", target_site=site2
            )

        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.copy_languages")

    def test_copy_announces_the_copy(self):
        page = create_page("Page", "nav_playground.html", "en")
        target = create_page("Target", "nav_playground.html", "en")

        new_page = page_services.copy_page_tree(
            page, target, "first-child", target_site=self.site, context=self.context
        )

        (kwargs,) = self.sent
        self.assertEqual((kwargs["operation"], kwargs["obj"], kwargs["new_page"]), (operations.COPY_PAGE, page, new_page))

    def test_a_system_context_without_a_user_can_copy(self):
        page = create_page("Page", "nav_playground.html", "en")
        system = OperationContext.system("tests")

        tree_copy = page_services.copy_page_tree(page, None, "last-child", target_site=self.site, context=system)
        source_copy = page_services.copy_page_from_source(
            page, target_site=self.site, parent_page=None, language="en", context=system
        )

        self.assertEqual(Page.objects.filter(pk__in=[tree_copy.pk, source_copy.pk]).count(), 2)
        self.assertEqual(tree_copy.get_content_obj("en").title, "Page")

    def test_the_last_translation_cannot_be_deleted(self):
        page = create_page("Page", "nav_playground.html", "en")

        with self.assertRaisesMessage(ValidationError, "There only exists one translation for this page"):
            page_services.delete_translation(page.get_content_obj("en"), context=self.context)
        self.assertEqual(page.get_languages(), ["en"])

    def test_a_translation_without_url_can_be_deleted(self):
        page = create_page("Page", "nav_playground.html", "en")
        german = create_page_content("de", "Seite", page)
        page.urls.filter(language="de").delete()

        page_services.delete_translation(german, context=self.context)

        self.assertEqual(list(page.pagecontent_set(manager="admin_manager").values_list("language", flat=True)), ["en"])

    def test_change_template_validates_the_template(self):
        page = create_page("Page", "nav_playground.html", "en")

        verdict = can(
            operations.CHANGE_PAGE_TEMPLATE, self.context, page_content=page.get_content_obj("en"), template="nope.html"
        )

        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.template_valid")

    def test_copy_language_needs_content_in_the_target_language(self):
        page = create_page("Page", "nav_playground.html", "en")

        with self.assertRaisesMessage(ValidationError, "The page has no content in the target language."):
            page_services.copy_language(page.get_content_obj("en"), "de", context=self.context)

    def test_copy_language_copies_nothing_when_one_placeholder_is_refused(self):
        page = create_page("Page", "nav_playground.html", "en")
        create_page_content("de", "Seite", page.reload(), template="nav_playground.html")
        source = page.get_content_obj("en")
        for slot in ("body", "right-column"):
            add_plugin(source.get_placeholders().get(slot=slot), "TextPlugin", "en", body=slot)
        refused_slot = "right-column"

        def has_add_plugins_permission(placeholder, user, plugins):
            return placeholder.slot != refused_slot

        with patch.object(Placeholder, "has_add_plugins_permission", has_add_plugins_permission):
            with self.assertRaises(PermissionDenied):
                page_services.copy_language(source, "de", context=self.context)

        self.assertFalse(CMSPlugin.objects.filter(language="de").exists())
        self.assertEqual(self.sent, [])

    def test_content_operations_announce_the_page_and_the_translation(self):
        page = create_page("Page", "nav_playground.html", "en")
        create_page_content("de", "Seite", page)
        content = page.get_content_obj("en")

        page_services.change_template(content, "nav_playground.html", context=self.context)
        page_services.toggle_in_navigation(content, context=self.context)
        page_services.copy_language(content, "de", context=self.context)

        self.assertEqual(
            [(kw["operation"], kw["obj"], kw["translation"]) for kw in self.sent],
            [
                (operations.CHANGE_PAGE_TEMPLATE, page, content),
                (operations.TOGGLE_PAGE_IN_NAVIGATION, page, content),
                (operations.COPY_PAGE_LANGUAGE, page, content),
            ],
        )

    def test_toggle_in_navigation_checks_permission(self):
        page = create_page("Page", "nav_playground.html", "en")
        staff = OperationContext(user=self._create_user("staff", is_staff=True))

        with self.assertRaises(PermissionDenied):
            page_services.toggle_in_navigation(page.get_content_obj("en"), context=staff)


class ContentPermissionTest(CMSTestCase):
    """``can_change_content`` lets a backend decide per translation."""

    def setUp(self):
        super().setUp()
        self.page = create_page("Page", "nav_playground.html", "en")
        self.german = create_page_content("de", "Seite", self.page.reload(), template="nav_playground.html")
        self.context = OperationContext(user=self.get_superuser())

    def only_english(self):
        class OnlyEnglish(PagePermissions):
            def can_change_content(self, page_content):
                return page_content.language == "en"

        return OnlyEnglish(self.context.user)

    def test_content_operations_ask_about_the_content(self):
        permissions = self.only_english()
        english = self.page.get_content_obj("en")

        self.assertTrue(
            can(operations.TOGGLE_PAGE_IN_NAVIGATION, self.context, page_content=english, permissions=permissions)
        )
        for operation_name, target in (
            (operations.TOGGLE_PAGE_IN_NAVIGATION, {}),
            (operations.CHANGE_PAGE_TEMPLATE, {"template": "nav_playground.html"}),
        ):
            with self.subTest(operation=operation_name):
                verdict = can(operation_name, self.context, page_content=self.german, permissions=permissions, **target)
                self.assertEqual([r.kind for r in verdict.reasons], ["permission"])

    def test_copy_language_asks_about_the_target(self):
        permissions = self.only_english()
        english = self.page.get_content_obj("en")

        self.assertFalse(
            can(
                operations.COPY_PAGE_LANGUAGE,
                self.context,
                page_content=english,
                target_language="de",
                permissions=permissions,
            )
        )
        self.assertTrue(
            can(
                operations.COPY_PAGE_LANGUAGE,
                self.context,
                page_content=self.german,
                target_language="en",
                permissions=permissions,
            )
        )

    def test_the_admin_decides_through_its_hook(self):
        class ReadOnlyGermanAdmin(PageContentAdmin):
            def has_change_permission(self, request, obj=None):
                if obj is not None and obj.language == "de":
                    return False
                return super().has_change_permission(request, obj)

        model_admin = ReadOnlyGermanAdmin(type(self.german), admin.site)
        with self.login_user_context(self.get_superuser()):
            request = self.get_request(post_data={"no": "data"})
            response = model_admin.change_innavigation(request, self.german.pk)
            self.assertEqual(response.status_code, 403)
            response = model_admin.change_innavigation(request, self.page.get_content_obj("en").pk)
            self.assertEqual(response.status_code, 204)


class AdminAddPermissionTest(CMSTestCase):
    """The page content admin's ``has_add_permission`` decides adds, but only as a veto."""

    def setUp(self):
        super().setUp()
        self.site = Site.objects.get_current()

    def adapter(self, user, allow):
        class Admin(PageContentAdmin):
            def has_add_permission(self, request):
                return allow

        request = self.get_request()
        request.user = user
        return AdminPageContentPermissions(Admin(PageContent, admin.site), request)

    def test_the_admin_can_refuse_an_add(self):
        user = self.get_superuser()
        context = OperationContext(user=user)
        permissions = self.adapter(user, allow=False)

        verdict = can(operations.ADD_PAGE, context, site=self.site, parent_page=None, permissions=permissions)

        self.assertFalse(verdict)
        self.assertEqual(verdict.reasons[0].name, "cms.pages.add_permission")
        with self.assertRaises(PermissionDenied):
            page_services.add_page(
                site=self.site,
                parent_page=None,
                source=None,
                language="en",
                content_data={"title": "new", "slug": "new", "path": "new", "template": "nav_playground.html"},
                context=context,
                permissions=permissions,
            )

    def test_the_admin_cannot_allow_an_add_on_its_own(self):
        # The hook only knows the query string's parent, not the parent the page gets.
        user = self._create_user("staff", is_staff=True)
        parent = create_page("Parent", "nav_playground.html", "en")

        for parent_page in (None, parent):
            with self.subTest(parent=parent_page):
                self.assertFalse(
                    can(
                        operations.ADD_PAGE,
                        OperationContext(user=user),
                        site=self.site,
                        parent_page=parent_page,
                        permissions=self.adapter(user, allow=True),
                    )
                )


class AdminPagePermissionHookTest(CMSTestCase):
    """The page admin's overridable hooks decide advanced settings and page permissions."""

    def setUp(self):
        super().setUp()
        self.page = create_page("Page", "nav_playground.html", "en")
        self.context = OperationContext(user=self.get_superuser())

        class LockedAdmin(PageAdmin):
            def has_change_advanced_settings_permission(self, request, obj=None):
                return False

            def has_change_permissions_permission(self, request, obj=None):
                return False

        request = self.get_request()
        request.user = self.context.user
        self.permissions = AdminPagePermissions(LockedAdmin(Page, admin.site), request)

    def test_advanced_settings(self):
        self.page.login_required = True
        with self.assertRaises(PermissionDenied):
            page_services.change_advanced_settings(self.page, context=self.context, permissions=self.permissions)
        self.page.refresh_from_db()
        self.assertFalse(self.page.login_required)

    def test_page_permissions(self):
        verdict = can(
            operations.CHANGE_PAGE_PERMISSIONS, self.context, page=self.page, permissions=self.permissions
        )
        self.assertEqual(verdict.reasons[0].name, "cms.pages.change_permissions_permission")
