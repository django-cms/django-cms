from unittest.mock import patch

from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import override as force_language

from cms import operations
from cms.api import add_plugin, create_page, create_page_content
from cms.cms_config import CMSCoreExtensions
from cms.models import CMSPlugin, Page, Placeholder
from cms.pages import services as page_services
from cms.pages.admin.forms import MovePageForm
from cms.pages.admin.page import PageContentAdmin
from cms.pages.permissions import PagePermissions
from cms.shared import checks
from cms.shared.checks import can
from cms.shared.operations import OperationContext, operation
from cms.signals import PAGE_OPERATION_SIGNALS, post_obj_operation, pre_obj_operation
from cms.test_utils.testcases import CMSTestCase

SLUG_NOT_UNIQUE = "You cannot have two pages with the same slug"


class RegistryIsolationMixin:
    """Keeps checks registered by a test out of the other tests."""

    def setUp(self):
        super().setUp()
        saved = {operation: dict(entries) for operation, entries in checks._extensions.items()}

        def restore():
            checks._extensions.clear()
            checks._extensions.update(saved)

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

    def test_a_silenced_context_announces_nothing(self):
        self.context = OperationContext(user=self.get_superuser(), emit_signals=False)
        with self.frame():
            pass
        self.assertEqual(self.sent, [])


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
