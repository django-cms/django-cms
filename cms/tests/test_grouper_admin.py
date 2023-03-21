
from django.contrib.admin import site
from django.templatetags.static import static
from django.utils.crypto import get_random_string

from cms.admin.utils import CONTENT_PREFIX
from cms.test_utils.project.sampleapp.models import (
    GrouperModel, GrouperModelContent,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils.i18n import get_language_list
from cms.utils.urlutils import admin_reverse, static_with_version


class SetupMixin:
    def setUp(self) -> None:
        self.grouper_instance = GrouperModel.objects.create(
            category_name="Grouper Category"
        )
        self.add_url = admin_reverse("sampleapp_groupermodel_add")
        self.change_url = admin_reverse("sampleapp_groupermodel_change", args=(self.grouper_instance.pk,))
        self.changelist_url = admin_reverse("sampleapp_groupermodel_changelist")
        self.admin_user = self.get_superuser()
        self.admin = site._registry[GrouperModel]

    def tearDown(self) -> None:
        self.grouper_instance.delete()
        self.admin.clear_content_cache()  # The admin does this automatically when items are added/deleted.

    def createContentInstance(self, language="en"):
        random_content = get_random_string(16)
        GrouperModelContent.objects.create(
            groupermodel=self.grouper_instance,
            language=language,
            secret_greeting=random_content,
        )
        self.admin.clear_content_cache()  # The admin does this automatically when items are added.
        return random_content


def wo_content_permission(method):
    """Decorator to temporarily switch of write permissions to content"""
    def inner(self, *args, **kwargs):
        self.admin.change_content = False
        try:
            return_value = method(self, *args, **kwargs)
        except Exception:
            raise
        finally:
            self.admin.change_content = True
        return return_value
    return inner


class ChangeListActionsTestCase(SetupMixin, CMSTestCase):
    def test_action_js_css(self):
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.changelist_url + "?language=en")
            self.assertContains(response, static("admin/js/jquery.init.js"))
            self.assertContains(response, static("cms/js/admin/actions.js"))
            self.assertContains(response, static_with_version("cms/css/cms.admin.css"))

    def test_add_action(self):
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.changelist_url + "?language=en")
            self.assertContains(response, 'class="cms-icon cms-icon-plus"')
            self.assertContains(response, f'href="/en/admin/sampleapp/groupermodel/{self.grouper_instance.pk}'
                                          f'/change/?language=en"')
            self.assertNotContains(response, 'class="cms-icon cms-icon-view"')

    def test_change_action(self):
        self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.changelist_url + "?language=en")
            self.assertContains(response, 'class="cms-icon cms-icon-view"')
            self.assertContains(response, f'href="/en/admin/sampleapp/groupermodel/{self.grouper_instance.pk}'
                                          f'/change/?language=en"')
            self.assertContains(response, 'class="cms-icon cms-icon-view"')


class GrouperModelAdminTestCase(SetupMixin, CMSTestCase):
    def test_form_class_created(self):
        """Tests if the form class has automatically been enhanced with the GrouperAdminFormMixin for
        the appropriate content model (actually its parent class _GrouperAdminFormMixin)"""
        from cms.admin.utils import _GrouperAdminFormMixin

        self.assertTrue(issubclass(self.admin.form, _GrouperAdminFormMixin))
        self.assertEqual(self.admin.form._content_model, GrouperModelContent)

    def test_form_class_content_fields(self):
        for field in self.admin.form._content_fields:
            self.assertIn(CONTENT_PREFIX + field, self.admin.form.base_fields)

    def test_content_model_detected(self) -> None:
        admin = site._registry[GrouperModel]
        self.assertEqual(admin.content_model, GrouperModelContent)


class GrouperChangeListTestCase(SetupMixin, CMSTestCase):
    def test_empty_content(self) -> None:
        """Without any content being created the changelist shows an empty content text"""
        with self.login_user_context(self.admin_user):
            for language in ("en", "de", "it"):
                response = self.client.get(self.changelist_url + f"?language={language}")
                self.assertContains(response, "Empty content")

    def test_with_content(self) -> None:
        """Create one content object and see if it appears in the right admin"""
        random_content = self.createContentInstance("de")
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.changelist_url + "?language=de")
            self.assertContains(response, "Grouper Category")
            self.assertContains(response, random_content)

            for language in ("en", "it"):
                response = self.client.get(self.changelist_url + f"?language={language}")
                self.assertContains(response, "Empty content")

    def test_with_content_only(self) -> None:
        """Create one content object and see if it appears in the right admin"""
        random_content = {lang: self.createContentInstance(lang) for lang in get_language_list()}
        with self.login_user_context(self.admin_user):
            for language in get_language_list():
                response = self.client.get(self.changelist_url + f"?language={language}")
                self.assertContains(response, "Grouper Category")
                self.assertContains(response, random_content[language])


class GrouperChangeTestCase(SetupMixin, CMSTestCase):
    def test_mixed_change_form(self):
        random_content = self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.change_url + "?language=en")
            # Contains relation to grouper as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__groupermodel" value="1" id="id_content__groupermodel">',
            )
            # Contains extra grouping field as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__language" value="en" id="id_content__language">',
            )
            # Contains grouper field with category (and its value)
            self.assertContains(
                response,
                '<input type="text" name="category_name" value="Grouper Category"',
            )
            # Contains content secret message as textarea
            self.assertContains(response, '<textarea name="content__secret_greeting"')
            self.assertContains(response, random_content)

    @wo_content_permission
    def test_change_form_wo_write_permit(self) -> None:
        random_content = self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.change_url + "?language=en")
            # Contains relation to grouper as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__groupermodel" value="1" id="id_content__groupermodel">',
            )
            # Contains extra grouping field as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__language" value="en" id="id_content__language">',
            )
            # Contains grouper field with category (and its value)
            self.assertContains(response, '<input type="text" name="category_name" value="Grouper Category"')
            # Contains content secret message as textarea
            self.assertContains(response, 'field-content__secret_greeting"')

            self.assertContains(response, random_content)

    def test_with_write_permit(self) -> None:
        # Request needed, but can_change_content not defined
        self.assertTrue(self.admin.change_content)
        self.assertNotIn("content__secret_greeting", self.admin.get_readonly_fields(None))

    @wo_content_permission
    def test_wo_write_permit(self) -> None:
        self.assertIn("content__secret_greeting", self.admin.get_readonly_fields(None))

    def test_save_grouper_model(self) -> None:
        ...

    def test_save_content_model(self) -> None:
        ...

    def test_create_grouper_model(self) -> None:
        ...

    def test_create_content_model(self) -> None:
        ...
