from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.test import override_settings

from cms import operations
from cms.api import add_plugin, create_page
from cms.core import services as plugin_services
from cms.core.permissions import PluginPermissions, get_permissions
from cms.models import (
    GlobalPagePermission,
    Page,
    PageContent,
    PagePermission,
    PageType,
    PageUrl,
    Placeholder,
    UserSettings,
)
from cms.pages import services as page_services
from cms.pages.permissions import PagePermissions, get_page_permissions
from cms.permissions import services as permission_services
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

    def test_plain_request_without_cms_path_still_emits(self):
        """Only the placeholder endpoints use cms_path; page endpoints do not."""
        request = self.get_request("/en/admin/cms/page/1/set-home/")
        request.user = self.get_superuser()

        context = OperationContext.from_request(request)

        self.assertTrue(context.emit_signals)
        self.assertIsNone(context.origin)


class PageDataValidationTest(CMSTestCase):
    """Forms, services and preflight share page validation before any mutation."""

    def setUp(self):
        super().setUp()
        self.user = self.get_superuser()
        self.context = OperationContext(user=self.user, language="en")
        self.page = create_page("Parent", "nav_playground.html", "en")
        self.content = self.page.get_admin_content("en")
        self.sent = []
        pre_obj_operation.connect(self.receive)
        self.addCleanup(pre_obj_operation.disconnect, self.receive)

    def receive(self, **kwargs):
        self.sent.append(kwargs)

    def counts(self):
        return tuple(model.objects.count() for model in (Page, PageContent, PageUrl, Placeholder))

    def assert_refused(self, operation, service, kwargs, field):
        before = self.counts()
        verdict = can(operation, self.context, **kwargs)
        self.assertFalse(verdict)
        self.assertTrue(verdict.complete, verdict.skipped)
        self.assertTrue(all(reason.kind == checks.VALIDATION for reason in verdict.reasons))
        with self.assertRaises(ValidationError) as caught:
            service(**kwargs, context=self.context)
        self.assertIn(field, caught.exception.message_dict)
        self.assertEqual([reason.message for reason in verdict.reasons], caught.exception.messages)
        self.assertEqual(before, self.counts())
        self.assertEqual(self.sent, [])

    def creation_kwargs(self, **changes):
        return {
            "site": self.page.site, "parent_page": None, "source": None, "language": "en",
            "content_data": {
                "title": "New", "slug": "new", "template": "nav_playground.html", **changes,
            },
        }

    def test_create_validates_field_values_before_signals(self):
        for field, value in (
            ("template", "missing.html"), ("title", "x" * 256),
            ("meta_description", "x" * 321), ("slug", "bad/slug"),
            ("redirect", "javascript:alert(1)/x"), ("limit_visibility_in_menu", 99),
            ("xframe_options", 99), ("overwrite_url", "<script>"),
        ):
            with self.subTest(field=field):
                self.assert_refused(
                    operations.ADD_PAGE, page_services.add_page,
                    self.creation_kwargs(**{field: value}), field,
                )

    def test_language_is_validated_for_pages_and_translations(self):
        kwargs = self.creation_kwargs()
        kwargs["language"] = "not-on-site"
        self.assert_refused(operations.ADD_PAGE, page_services.add_page, kwargs, "language")
        self.assert_refused(
            operations.ADD_PAGE_TRANSLATION, page_services.add_translation,
            {"page": self.page, "language": "not-on-site", "content_data": kwargs["content_data"]},
            "language",
        )

    def test_duplicate_slug_and_overwrite_url_are_field_errors(self):
        for values, field in (
            ({"slug": self.content.slug}, "slug"),
            ({"overwrite_url": self.page.get_path("en")}, "overwrite_url"),
        ):
            with self.subTest(field=field):
                self.assert_refused(
                    operations.ADD_PAGE, page_services.add_page, self.creation_kwargs(**values), field,
                )

    def test_change_validates_fields_and_leaves_content_unchanged(self):
        other = create_page("Other", "nav_playground.html", "en")
        original = self.content.title
        for data, field in (
            ({"title": "x" * 256}, "title"),
            ({"template": "bad.html"}, "template"),
            ({"limit_visibility_in_menu": 99}, "limit_visibility_in_menu"),
            ({"xframe_options": 99}, "xframe_options"),
            ({"slug": "other"}, "slug"),
            ({"overwrite_url": other.get_path("en")}, "overwrite_url"),
            ({"page": other}, "page"),
        ):
            with self.subTest(field=field):
                self.assert_refused(
                    operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
                    {"page_content": self.content, "data": data}, field,
                )
                self.content.refresh_from_db()
                self.assertEqual(self.content.title, original)

    def test_sibling_slug_conflicts_on_change(self):
        first = create_page("First", "nav_playground.html", "en", parent=self.page)
        second = create_page("Second", "nav_playground.html", "en", parent=self.page)
        self.assert_refused(
            operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
            {"page_content": second.get_admin_content("en"), "data": {"slug": first.get_slug("en")}},
            "slug",
        )

    def test_template_must_be_loadable(self):
        with self.settings(CMS_TEMPLATES=[("not-installed.html", "Missing")]):
            self.assert_refused(
                operations.ADD_PAGE, page_services.add_page,
                self.creation_kwargs(template="not-installed.html"), "template",
            )

    def test_advanced_settings_validate_reverse_id_and_namespace(self):
        create_page(
            "Other", "nav_playground.html", "en",
            reverse_id="taken", apphook="SampleApp", apphook_namespace="taken",
        )
        for data, field in (
            ({"reverse_id": "taken"}, "reverse_id"),
            ({"application_urls": "SampleApp", "application_namespace": "taken"}, "application_namespace"),
            ({"application_urls": "NoSuchApp"}, "application_urls"),
            ({"site": self.page.site}, "site"),
        ):
            with self.subTest(field=field):
                self.assert_refused(
                    operations.CHANGE_PAGE_ADVANCED_SETTINGS, page_services.change_advanced_settings,
                    {"page": self.page, "data": data}, field,
                )

    def test_config_zero_is_validated_like_string_zero(self):
        from cms.pages.apphook_pool import apphook_pool
        from cms.test_utils.project.sampleapp.models import SampleAppConfig

        app = SimpleNamespace(
            app_config=SampleAppConfig, app_name="fallback",
            get_configs=SampleAppConfig.objects.all,
        )
        with patch.object(apphook_pool, "discover_apps"), patch.object(apphook_pool, "get_apphook", return_value=app):
            for config in (0, "0"):
                with self.subTest(config=config):
                    self.assert_refused(
                        operations.CHANGE_PAGE_ADVANCED_SETTINGS, page_services.change_advanced_settings,
                        {"page": self.page, "data": {"application_urls": "ConfiguredApp", "application_configs": config}},
                        "application_configs",
                    )
            for config in (None, ""):
                with self.subTest(config=config):
                    page = page_services.change_advanced_settings(
                        self.page, data={"application_urls": "ConfiguredApp", "application_configs": config},
                        context=self.context,
                    )
                    self.assertEqual(page.application_namespace, "fallback")

    def test_advanced_settings_only_save_changed_fields_and_audit_fields(self):
        original_save = Page.save

        def save_after_unrelated_update(page, **kwargs):
            Page.objects.filter(pk=page.pk).update(login_required=True)
            return original_save(page, **kwargs)

        with patch.object(Page, "save", save_after_unrelated_update):
            page_services.change_advanced_settings(self.page, data={"reverse_id": "changed"}, context=self.context)
        self.page.refresh_from_db()
        self.assertTrue(self.page.login_required)
        self.assertEqual(self.page.reverse_id, "changed")

    def test_advanced_settings_instance_compatibility_also_validates(self):
        create_page("Other", "nav_playground.html", "en", reverse_id="taken")
        self.page.reverse_id = "taken"
        with self.assertRaises(ValidationError) as caught:
            page_services.change_advanced_settings(self.page, context=self.context)
        self.assertIn("reverse_id", caught.exception.message_dict)
        self.page.refresh_from_db()
        self.assertIsNone(self.page.reverse_id)

    @override_settings(CMS_APPHOOKS=["cms.test_utils.project.sampleapp.cms_apps.SampleAppWithConfig"])
    def test_apphook_configuration_is_validated_and_normalized(self):
        from cms.test_utils.project.sampleapp.models import SampleAppConfig

        config_binding = patch.object(SampleAppConfig, "cmsapp", None, create=True)
        config_binding.start()
        self.addCleanup(config_binding.stop)
        self.apphook_clear()
        self.addCleanup(self.apphook_clear)
        config = SampleAppConfig.objects.create(namespace="configured")
        kwargs = {
            "page": self.page,
            "data": {"application_urls": "SampleAppWithConfig", "application_configs": "not-an-id"},
        }
        self.assert_refused(
            operations.CHANGE_PAGE_ADVANCED_SETTINGS, page_services.change_advanced_settings,
            kwargs, "application_configs",
        )
        kwargs["data"]["application_configs"] = config.pk
        self.assertTrue(can(operations.CHANGE_PAGE_ADVANCED_SETTINGS, self.context, **kwargs))
        changed = page_services.change_advanced_settings(**kwargs, context=self.context)
        self.assertEqual(changed.application_namespace, "configured")
        self.assertNotIn("application_namespace", kwargs["data"])  # input is not mutated

    def test_invalid_override_is_rejected_even_for_home_or_unreachable_page(self):
        self.page.set_as_homepage(self.user)
        self.content.page = self.page
        self.assert_refused(
            operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
            {"page_content": self.content, "data": {"overwrite_url": "<bad>"}}, "overwrite_url",
        )
        child = create_page("Child", "nav_playground.html", "en", parent=self.page)
        self.page.is_home = False
        self.page.save()
        self.page.urls.update(path=None)
        child_content = child.get_admin_content("en")
        self.assert_refused(
            operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
            {"page_content": child_content, "data": {"overwrite_url": "bad/<path>"}}, "overwrite_url",
        )

    def test_context_api_uses_field_errors_and_legacy_api_keeps_assertions(self):
        from cms.api import create_page_content

        with self.assertRaises(ValidationError) as caught:
            create_page_content("de", "Other", self.page, template="bad.html", context=self.context)
        self.assertIn("template", caught.exception.message_dict)
        self.assertEqual(self.sent, [])
        with self.assertRaises(AssertionError):
            create_page_content("de", "Other", self.page, template="bad.html")

    def test_context_page_api_validates_before_signals_or_rows(self):
        create_page("Other", "nav_playground.html", "en", reverse_id="taken")
        for values, field in (
            ({"template": "bad.html"}, "template"),
            ({"language": "not-on-site"}, "language"),
            ({"reverse_id": "taken"}, "reverse_id"),
            ({"apphook": "NoSuchApp"}, "application_urls"),
            ({"position": "invalid"}, "position"),
            ({"navigation_extenders": "NoSuchMenu"}, "navigation_extenders"),
        ):
            with self.subTest(field=field):
                before = self.counts()
                with self.assertRaises(ValidationError) as caught:
                    create_page(**{
                        "title": "New", "template": "nav_playground.html", "language": "en",
                        "context": self.context, **values,
                    })
                self.assertIn(field, caught.exception.message_dict)
                self.assertEqual(before, self.counts())
                self.assertEqual(self.sent, [])

    def test_context_page_api_checks_sibling_site_in_system_context(self):
        other_site = Site.objects.create(domain="other.example", name="Other")
        before = self.counts()
        with self.assertRaises(ValidationError) as caught:
            create_page(
                "New", "nav_playground.html", "en", parent=self.page, position="right",
                site=other_site, context=OperationContext.system("test.import"),
            )
        self.assertIn("parent_page", caught.exception.message_dict)
        self.assertEqual(before, self.counts())
        self.assertEqual(self.sent, [])

    def test_translation_data_and_duplicate_language_are_checked(self):
        for language, data, field in (
            ("de", {"title": "Neu", "template": "bad.html"}, "template"),
            ("de", {"title": "Neu", "limit_visibility_in_menu": 99}, "limit_visibility_in_menu"),
            ("en", {"title": "Duplicate"}, "language"),
        ):
            with self.subTest(field=field):
                self.assert_refused(
                    operations.ADD_PAGE_TRANSLATION, page_services.add_translation,
                    {"page": self.page, "language": language, "content_data": data}, field,
                )

    def test_headless_template_choices_and_inheritance(self):
        from cms.constants import TEMPLATE_INHERITANCE_MAGIC

        with self.settings(CMS_TEMPLATES=[], CMS_PLACEHOLDERS=[("headless", ["body"], "Headless")]):
            for template in ("headless", TEMPLATE_INHERITANCE_MAGIC):
                kwargs = self.creation_kwargs(template=template, slug=f"new-{template}")
                self.assertTrue(can(operations.ADD_PAGE, self.context, **kwargs))
                content = page_services.add_page(**kwargs, context=self.context)
                self.assertEqual(content.template, template)
            self.sent.clear()
            self.assert_refused(
                operations.ADD_PAGE, page_services.add_page,
                self.creation_kwargs(template="missing"), "template",
            )

    def test_template_change_and_content_edit_share_validation(self):
        for service, operation, data in (
            (page_services.change_template, operations.CHANGE_PAGE_TEMPLATE, {"template": "bad.html"}),
            (page_services.change_page_content, operations.CHANGE_PAGE_TRANSLATION,
             {"data": {"template": "bad.html"}}),
        ):
            self.assert_refused(operation, service, {"page_content": self.content, **data}, "template")

    def test_prepared_values_do_not_modify_input_and_normalize_overwrite_url(self):
        kwargs = self.creation_kwargs(overwrite_url="/custom/path/")
        self.assertTrue(can(operations.ADD_PAGE, self.context, **kwargs))
        self.assertEqual(kwargs["content_data"]["overwrite_url"], "/custom/path/")
        content = page_services.add_page(**kwargs, context=self.context)
        self.assertEqual(content.overwrite_url, "custom/path")
        self.assertEqual(content.page.get_path("en"), "custom/path")
        self.assertEqual(kwargs["content_data"]["overwrite_url"], "/custom/path/")

    def test_page_type_preflight_uses_its_future_root_without_creating_it(self):
        from cms.constants import PAGE_TYPES_ID

        kwargs = self.creation_kwargs(slug=self.content.slug)
        kwargs["is_page_type"] = True
        before = self.counts()
        verdict = can(operations.ADD_PAGE, self.context, **kwargs)
        self.assertTrue(verdict, verdict.reasons)
        self.assertTrue(verdict.complete)
        self.assertEqual(before, self.counts())
        content = page_services.add_page(**kwargs, context=self.context)
        self.assertEqual(content.page.get_path("en"), f"{PAGE_TYPES_ID}/{self.content.slug}")
        self.sent.clear()
        # The same preflight must use the now-existing root as well.
        self.assert_refused(operations.ADD_PAGE, page_services.add_page, kwargs, "slug")

    def test_missing_data_is_reported_as_skipped(self):
        for operation, kwargs in (
            (operations.ADD_PAGE, {"site": self.page.site}),
            (operations.ADD_PAGE_TRANSLATION, {"page": self.page}),
            (operations.CHANGE_PAGE_TRANSLATION, {"page_content": self.content}),
            (operations.CHANGE_PAGE_ADVANCED_SETTINGS, {"page": self.page}),
        ):
            with self.subTest(operation=operation):
                verdict = can(operation, self.context, **kwargs)
                self.assertTrue(verdict)
                self.assertFalse(verdict.complete)
                self.assertIn("cms.pages.content_data_valid", verdict.skipped)

    def test_forms_report_the_same_field_errors(self):
        from cms.pages.admin.forms import AddPageForm, AdvancedSettingsForm, ChangePageForm

        request = self.get_request("/?language=en")
        request.user = self.user
        create_page("Other", "nav_playground.html", "en", reverse_id="taken")
        cases = (
            (AddPageForm, None, {"title": "New", "slug": "parent"}, "slug",
             page_services.add_page, self.creation_kwargs(slug="parent")),
            (ChangePageForm, self.content, {"title": "Parent", "slug": "parent", "overwrite_url": "<bad>"},
             "overwrite_url", page_services.change_page_content,
             {"page_content": self.content, "data": {"overwrite_url": "<bad>"}}),
            (AdvancedSettingsForm, self.page, {"reverse_id": "taken"}, "reverse_id",
             page_services.change_advanced_settings, {"page": self.page, "data": {"reverse_id": "taken"}}),
        )
        for base, instance, data, field, service, kwargs in cases:
            with self.subTest(form=base.__name__):
                form_class = type("BoundForm", (base,), {"_site": self.page.site, "_request": request})
                form = form_class(data=data, instance=instance)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)
                with self.assertRaises(ValidationError) as caught:
                    service(**kwargs, context=self.context)
                self.assertEqual(list(form.errors[field]), caught.exception.message_dict[field])

    def test_validation_does_not_depend_on_assertions(self):
        # Can also be run manually with python -O; CI uses normal Python.
        self.assert_refused(
            operations.ADD_PAGE, page_services.add_page,
            self.creation_kwargs(template="bad.html"), "template",
        )

    def test_extended_admin_forms_keep_extra_fields_and_save_core_fields(self):
        from django import forms

        from cms.pages.admin.forms import AdvancedSettingsForm, ChangePageForm

        request = self.get_request("/?language=en")
        request.user = self.user
        for base, instance, data in (
            (ChangePageForm, self.content, {"title": "Updated", "slug": "parent"}),
            (AdvancedSettingsForm, self.page, {"reverse_id": "updated"}),
        ):
            with self.subTest(form=base.__name__):
                form_class = type("ExtendedForm", (base,), {
                    "_site": self.page.site, "_request": request, "seo_note": forms.CharField(),
                })
                form = form_class(data={**data, "seo_note": "Keep me"}, instance=instance)
                self.assertTrue(form.is_valid(), form.errors)
                form.save()
                self.assertEqual(form.cleaned_data["seo_note"], "Keep me")
                instance.refresh_from_db()
                for field, value in data.items():
                    self.assertEqual(getattr(instance, field), value)

    def test_form_conflict_link_uses_the_requests_language(self):
        from cms.pages.admin.forms import ChangePageForm

        other = create_page("Other", "nav_playground.html", "en")
        request = self.get_request("/?language=de")
        request.user = self.user
        form_class = type("BoundForm", (ChangePageForm,), {"_site": self.page.site, "_request": request})
        form = form_class(data={"title": "Changed", "slug": other.get_slug("en")}, instance=self.content)
        self.assertFalse(form.is_valid())
        self.assertIn("?language=de", form.errors["slug"][0])

    def replace_data_checks(self):
        self.enterContext(patch.dict(checks._extensions, {}, clear=True))
        for name in (
            operations.ADD_PAGE, operations.ADD_PAGE_TRANSLATION,
            operations.CHANGE_PAGE_TRANSLATION, operations.CHANGE_PAGE_ADVANCED_SETTINGS,
        ):
            checks.register_check(name, "cms.pages.content_data_valid", lambda context, **kwargs: None)

    def test_replaced_data_checks_do_not_break_services_or_context_apis(self):
        from cms.api import create_page_content

        self.replace_data_checks()
        content = page_services.add_page(**self.creation_kwargs(), context=self.context)
        translated = page_services.add_translation(
            self.page, language="de", content_data={"title": "Deutsch"}, context=self.context,
        )
        self.assertEqual(translated.template, self.content.template)
        changed = page_services.change_page_content(content, data={"title": "Changed"}, context=self.context)
        self.assertEqual(changed.title, "Changed")
        page = page_services.change_advanced_settings(
            self.page, data={"reverse_id": "changed"}, context=self.context,
        )
        self.assertEqual(page.reverse_id, "changed")
        api_page = create_page("API", "nav_playground.html", "en", context=self.context)
        api_content = create_page_content("de", "API Deutsch", api_page, context=self.context)
        self.assertEqual(api_content.language, "de")

    def test_replaced_data_checks_still_reject_unsupported_input_shapes(self):
        from cms.api import create_page_content

        self.replace_data_checks()
        for call in (
            lambda: page_services.add_page(**self.creation_kwargs(unknown=True), context=self.context),
            lambda: page_services.add_translation(
                self.page, language="de", content_data={"title": "New", "unknown": True}, context=self.context,
            ),
            lambda: page_services.change_page_content(
                self.content, data={"unknown": True}, context=self.context,
            ),
            lambda: page_services.change_advanced_settings(
                self.page, data={"unknown": True}, context=self.context,
            ),
            lambda: create_page(
                "New", "nav_playground.html", "en", limit_visibility_in_menu="not-an-integer", context=self.context,
            ),
            lambda: create_page_content(
                "de", "New", self.page, limit_visibility_in_menu="not-an-integer", context=self.context,
            ),
        ):
            before = self.counts()
            with self.assertRaises(ValidationError):
                call()
            self.assertEqual(self.counts(), before)
            self.assertEqual(self.sent, [])

    def test_page_data_is_prepared_once_with_or_without_replaced_check(self):
        from cms.pages import validation

        for replaced in (False, True):
            with self.subTest(replaced=replaced):
                if replaced:
                    self.replace_data_checks()
                with patch.object(
                    validation, "prepare_content_change", wraps=validation.prepare_content_change,
                ) as prepare:
                    page_services.change_page_content(self.content, data={"title": "Changed"}, context=self.context)
                self.assertEqual(prepare.call_count, 1)

    def test_replacement_owns_description_limit_in_preflight_and_execution(self):
        from cms.api import create_page_content

        data = {"meta_description": "x" * 400, "overwrite_url": "/custom/path/"}
        self.assert_refused(
            operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
            {"page_content": self.content, "data": data}, "meta_description",
        )
        self.assert_refused(
            operations.ADD_PAGE, page_services.add_page,
            self.creation_kwargs(meta_description="x" * 400), "meta_description",
        )
        self.assert_refused(
            operations.ADD_PAGE_TRANSLATION, page_services.add_translation,
            {"page": self.page, "language": "de", "content_data": {"title": "Deutsch", "meta_description": "x" * 400}},
            "meta_description",
        )
        self.replace_data_checks()
        observed = []

        def allow_longer_description(context, *, prepared, **kwargs):
            values = prepared.get("data", prepared.get("content_data"))
            observed.append(dict(values))
            if len(values.get("meta_description") or "") > 500:
                raise ValidationError({"meta_description": "At most 500 characters."})

        for operation in (
            operations.ADD_PAGE, operations.ADD_PAGE_TRANSLATION, operations.CHANGE_PAGE_TRANSLATION,
        ):
            checks.register_check(operation, "cms.pages.content_data_valid", allow_longer_description)

        verdict = can(
            operations.CHANGE_PAGE_TRANSLATION, self.context, page_content=self.content, data=data,
        )
        self.assertTrue(verdict)
        self.assertTrue(verdict.complete)
        page_services.change_page_content(self.content, data=data, context=self.context)
        self.content.refresh_from_db()
        self.assertEqual(self.content.meta_description, data["meta_description"])
        self.assertEqual(self.content.overwrite_url, "custom/path")
        self.assertEqual(observed[-2], observed[-1])
        self.assertEqual(data["overwrite_url"], "/custom/path/")  # no caller mutation

        kwargs = self.creation_kwargs(meta_description="x" * 400)
        verdict = can(operations.ADD_PAGE, self.context, **kwargs)
        self.assertTrue(verdict)
        self.assertTrue(verdict.complete)
        created = page_services.add_page(**kwargs, context=self.context)
        self.assertEqual(created.meta_description, "x" * 400)
        self.assertEqual(observed[-2], observed[-1])
        translated_kwargs = {"page": self.page, "language": "de", "content_data": {
            "title": "Deutsch", "meta_description": "x" * 400,
        }}
        verdict = can(operations.ADD_PAGE_TRANSLATION, self.context, **translated_kwargs)
        self.assertTrue(verdict)
        self.assertTrue(verdict.complete)
        translated = page_services.add_translation(**translated_kwargs, context=self.context)
        self.assertEqual(translated.meta_description, "x" * 400)
        self.assertEqual(translated.template, self.content.template)
        self.assertEqual(observed[-2], observed[-1])

        api_page = create_page("API", "nav_playground.html", "en", meta_description="x" * 400, context=self.context)
        self.assertEqual(api_page.get_admin_content("en").meta_description, "x" * 400)
        api_translation = create_page_content(
            "de", "API Deutsch", api_page, meta_description="x" * 400, context=self.context,
        )
        self.assertEqual(api_translation.meta_description, "x" * 400)

        self.sent.clear()
        self.assert_refused(
            operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
            {"page_content": self.content, "data": {"meta_description": "x" * 501}}, "meta_description",
        )

    def test_replacement_can_relax_advanced_settings_uniqueness(self):
        create_page("Other", "nav_playground.html", "en", reverse_id="shared")
        kwargs = {"page": self.page, "data": {"reverse_id": "shared"}}
        self.assert_refused(
            operations.CHANGE_PAGE_ADVANCED_SETTINGS, page_services.change_advanced_settings, kwargs, "reverse_id",
        )
        self.replace_data_checks()
        verdict = can(operations.CHANGE_PAGE_ADVANCED_SETTINGS, self.context, **kwargs)
        self.assertTrue(verdict)
        self.assertTrue(verdict.complete)
        changed = page_services.change_advanced_settings(**kwargs, context=self.context)
        self.assertEqual(changed.reverse_id, "shared")

    def test_database_url_conflict_rolls_back_and_becomes_field_error(self):
        # Replacing validation cannot remove the database's routing constraint.
        self.replace_data_checks()
        for values, field in (({"slug": "parent"}, "slug"), ({"overwrite_url": "parent"}, "overwrite_url")):
            with self.subTest(field=field):
                before = self.counts()
                with self.assertRaises(ValidationError) as caught:
                    page_services.add_page(**self.creation_kwargs(**values), context=self.context)
                self.assertIn(field, caught.exception.message_dict)
                self.assertEqual(self.counts(), before)

    def test_unrelated_integrity_error_is_not_translated(self):
        error = IntegrityError("An unrelated constraint failed")
        before = self.counts()
        with patch("cms.api._create_page_content", side_effect=error):
            with self.assertRaises(IntegrityError) as caught:
                page_services.add_page(**self.creation_kwargs(), context=self.context)
        self.assertIs(caught.exception, error)
        self.assertEqual(self.counts(), before)

    def test_descendant_url_collision_rolls_back_content_and_urls(self):
        child = create_page("Child", "nav_playground.html", "en", parent=self.page)
        create_page("Override", "nav_playground.html", "en", overwrite_url="renamed/child")
        with self.assertRaises(ValidationError) as caught:
            page_services.change_page_content(self.content, data={"slug": "renamed"}, context=self.context)
        self.assertIn("slug", caught.exception.message_dict)
        self.content.refresh_from_db()
        self.assertEqual(self.content.slug, "parent")
        self.assertEqual(PageUrl.objects.get(page=self.page, language="en").path, "parent")
        self.assertEqual(PageUrl.objects.get(page=child, language="en").path, "parent/child")

    def test_shape_errors_also_appear_in_preflight_with_replaced_checks(self):
        self.replace_data_checks()
        self.assert_refused(
            operations.CHANGE_PAGE_TRANSLATION, page_services.change_page_content,
            {"page_content": self.content, "data": {"unknown": "value"}}, "unknown",
        )

    def test_preparation_waits_for_permissions_in_preflight_and_execution(self):
        from cms.pages import validation

        context = OperationContext(user=self.get_staff_user_with_no_permissions())
        with patch.object(validation, "prepare_content_change", wraps=validation.prepare_content_change) as prepare:
            self.assertFalse(can(
                operations.CHANGE_PAGE_TRANSLATION, context, page_content=self.content, data={"title": "Changed"},
            ))
            with self.assertRaises(PermissionDenied):
                page_services.change_page_content(self.content, data={"title": "Changed"}, context=context)
        prepare.assert_not_called()

    def test_preflight_prepares_once_without_writing_or_mutating_input(self):
        from cms.pages import validation

        data = {"overwrite_url": "/prepared/path/"}
        before = self.counts()
        with patch.object(validation, "prepare_content_change", wraps=validation.prepare_content_change) as prepare:
            verdict = can(
                operations.CHANGE_PAGE_TRANSLATION, self.context, page_content=self.content, data=data,
            )
        self.assertTrue(verdict)
        self.assertTrue(verdict.complete)
        self.assertEqual(prepare.call_count, 1)
        self.assertEqual(data, {"overwrite_url": "/prepared/path/"})
        self.assertEqual(before, self.counts())
        self.assertEqual(self.sent, [])


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
            permission_services.save_page_permissions(self.page, context=context)
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
            permission_services.set_user_permissions({"can_add_page": True}, actor, context=context)
        grant = GlobalPagePermission(user=actor, can_add=True, can_change=True)
        with self.assertRaises(PermissionDenied):
            permission_services.save_global_page_permission(grant, sites=[Site.objects.get_current()], context=context)
        self.assertFalse(GlobalPagePermission.objects.filter(user=actor).exists())

    def test_permission_services_apply_and_remove_grants(self):
        actor = self.get_staff_user_with_no_permissions()
        page_grant = PagePermission(user=actor, page=self.page)
        permission_services.save_page_permissions(self.page, save=[page_grant], context=self._context())
        self.assertTrue(PagePermission.objects.filter(pk=page_grant.pk).exists())
        permission_services.save_page_permissions(self.page, delete=[page_grant], context=self._context())
        self.assertFalse(PagePermission.objects.filter(pk=page_grant.pk).exists())

        global_grant = GlobalPagePermission(user=actor)
        site = Site.objects.get_current()
        permission_services.save_global_page_permission(global_grant, sites=[site], context=self._context())
        self.assertEqual(list(global_grant.sites.all()), [site])
        permission_services.delete_global_page_permissions([global_grant], context=self._context())
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
        parent = add_plugin(self.other, "ColumnPlugin", "en")

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
            permission_services.set_user_permissions({"can_add_page": True}, self.staff.user)

    def test_a_system_context_grants_without_permission_checks(self):
        target = self._create_user("target", is_staff=True)

        permission_services.set_user_permissions(
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
            permission_services.save_page_permissions(self.page, delete=[grant], context=self.admin)
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
            permission_services.delete_global_page_permissions([first, second], context=self.admin)
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
        self.assertEqual(verdict.reasons[0].name, "cms.permissions.grant_recipients")

    def test_view_restrictions_may_name_anyone(self):
        verdict = self.verdict(can_view=True)

        self.assertNotIn("cms.permissions.grant_recipients", [reason.name for reason in verdict.reasons])


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
