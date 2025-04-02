
from django.contrib.admin import site
from django.templatetags.static import static
from django.utils.crypto import get_random_string

from cms.admin.utils import CONTENT_PREFIX
from cms.test_utils.project.sampleapp.models import (
    GrouperModel,
    GrouperModelContent,
    SimpleGrouperModel,
    SimpleGrouperModelContent,
)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.grouper import wo_content_permission
from cms.utils.i18n import get_language_list
from cms.utils.urlutils import admin_reverse, static_with_version


class SetupMixin:
    """Create one grouper object and retrieve the admin instance"""
    def setUp(self) -> None:
        self.grouper_instance = GrouperModel.objects.create(
            category_name="Grouper Category"
        )
        self.add_url = admin_reverse("sampleapp_groupermodel_add")
        self.change_url = admin_reverse("sampleapp_groupermodel_change", args=(self.grouper_instance.pk,))
        self.changelist_url = admin_reverse("sampleapp_groupermodel_changelist")
        self.admin_user = self.get_superuser()
        self.admin = site._registry[GrouperModel]
        self.groupermodel = "groupermodel"
        self.grouper_model = "grouper_model"

    def tearDown(self) -> None:
        self.grouper_instance.delete()
        self.admin.clear_content_cache()  # The admin does this automatically for each new request.

    def createContentInstance(self, language="en"):
        """Creates a content instance with a random content for a language. The random content is returned
        to be able to check if it appears in forms etc."""
        instance = GrouperModelContent.objects.create(
            grouper_model=self.grouper_instance,
            language=language,
            secret_greeting=get_random_string(16),
        )
        self.admin.clear_content_cache()  # The admin does this automatically for each new request.
        return instance


class SimpleSetupMixin:
    """Create one grouper object and retrieve the admin instance"""
    def setUp(self) -> None:
        self.grouper_instance = SimpleGrouperModel.objects.create(
            category_name="Grouper Category"
        )
        self.add_url = admin_reverse("sampleapp_simplegroupermodel_add")
        self.change_url = admin_reverse("sampleapp_simplegroupermodel_change", args=(self.grouper_instance.pk,))
        self.changelist_url = admin_reverse("sampleapp_simplegroupermodel_changelist")
        self.admin_user = self.get_superuser()
        self.admin = site._registry[SimpleGrouperModel]
        self.groupermodel = "simplegroupermodel"
        self.grouper_model = "simple_grouper_model"

    def tearDown(self) -> None:
        self.grouper_instance.delete()
        self.admin.clear_content_cache()  # The admin does this automatically for each new request.

    def createContentInstance(self, language="en"):
        """Creates a content instance with a random content for a language. The random content is returned
        to be able to check if it appears in forms etc."""

        assert language == "en", "Only English is supported for SimpleGrouperModelContent"
        instance = SimpleGrouperModelContent.objects.create(
            simple_grouper_model=self.grouper_instance,
            secret_greeting=get_random_string(16),
        )
        self.admin.clear_content_cache()  # The admin does this automatically for each new request.
        return instance


class SimpleChangeListActionsTestCase(SimpleSetupMixin, CMSTestCase):
    def test_action_js_css(self):
        """Are js and css files loaded?
        The js and css files are supposed to be arranged by the GrouperAdminMixin."""
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(f"{self.changelist_url}?", follow=True)
            # Assert
            self.assertContains(response, static("admin/js/jquery.init.js"))
            self.assertContains(response, static("cms/js/admin/actions.js"))
            self.assertContains(response, static_with_version("cms/css/cms.admin.css"))

    def test_add_action(self):
        """Change list offers an add button if no content object exists for grouper.
        The button is supposed to be arranged by the GrouperAdminMixin."""
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(f"{self.changelist_url}?language=en", follow=True)
            # Assert
            self.assertContains(response, 'class="cms-icon cms-icon-plus"')
            self.assertContains(response, f'href="/en/admin/sampleapp/{self.groupermodel}/{self.grouper_instance.pk}'
                                          f'/change/?')
            self.assertNotContains(response, 'class="cms-icon cms-icon-view"')

    def test_change_action(self):
        """Change list offers a settings button if content object exists for grouper"""
        # Arrange
        self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(f"{self.changelist_url}?language=en", follow=True)
            # Assert
            self.assertContains(response, 'class="cms-icon cms-icon-view"')
            self.assertContains(response, f'href="/en/admin/sampleapp/{self.groupermodel}/{self.grouper_instance.pk}'
                                          f'/change/?')
            self.assertContains(response, 'class="cms-icon cms-icon-view"')

    def test_get_action(self):
        admin = site._registry[GrouperModel]

        get_action = admin.admin_action_button(
            "/some/url",
            icon="info",
            title="Info",
            action="get",
        )
        self.assertIn("cms-form-get-method", get_action)
        self.assertNotIn("cms-form-post-method", get_action)

    def test_post_action(self):
        admin = site._registry[GrouperModel]

        get_action = admin.admin_action_button(
            "/some/url",
            icon="bin",
            title="Delete",
            action="post",
        )
        self.assertNotIn("cms-form-get-method", get_action)
        self.assertIn("cms-form-post-method", get_action)


class ChangeListActionsTestCase(SetupMixin, SimpleChangeListActionsTestCase):
    pass


class GrouperModelAdminTestCase(SetupMixin, CMSTestCase):
    def test_form_class_created(self):
        """The form class has automatically been enhanced with the GrouperAdminFormMixin for
        the appropriate content model (actually its parent class _GrouperAdminFormMixin)"""
        # Arrange
        from cms.admin.utils import _GrouperAdminFormMixin

        # Assert
        self.assertTrue(issubclass(self.admin.form, _GrouperAdminFormMixin))
        self.assertEqual(self.admin.form._content_model, GrouperModelContent)

    def test_form_class_content_fields(self):
        """The content fields appear in the admin form with a prefix"""
        # Assert
        for field in self.admin.form._content_fields:
            self.assertIn(CONTENT_PREFIX + field, self.admin.form.base_fields)

    def test_content_model_detected(self) -> None:
        """Content model has been detected correctly for grouper admin"""
        # Assert
        admin = site._registry[GrouperModel]
        self.assertEqual(admin.content_model, GrouperModelContent)


class GrouperChangeListTestCase(SetupMixin, CMSTestCase):
    def test_language_selector(self):
        """All languages available to select"""
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.get(self.changelist_url)
        # Assert
        for lang, verb in self.admin.get_language_tuple():
            self.assertContains(response, f'<option value="{lang}"')

    def test_empty_content(self) -> None:
        """Without any content being created the changelist shows an empty content text"""
        with self.login_user_context(self.admin_user):
            for language in ("en", "de", "it"):
                # Act
                response = self.client.get(self.changelist_url + f"?language={language}")
                # Assert
                self.assertContains(response, "Empty content")

    def test_with_content(self) -> None:
        """Create one content object and see if it appears in the right admin"""
        # Arrange
        random_content = self.createContentInstance("de")
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(self.changelist_url + "?language=de")
            # Assert
            self.assertContains(response, "Grouper Category")
            self.assertContains(response, random_content.secret_greeting)

            for language in ("en", "it"):
                # Act
                response = self.client.get(self.changelist_url + f"?language={language}")
                # Assert
                self.assertContains(response, "Empty content")

    def test_with_content_only(self) -> None:
        """Create one content object and see if it appears in the right admin"""
        # Arrange
        random_content = {lang: self.createContentInstance(lang).secret_greeting for lang in get_language_list()}
        with self.login_user_context(self.admin_user):
            for language in get_language_list():
                # Act
                response = self.client.get(self.changelist_url + f"?language={language}")
                # Assert
                self.assertContains(response, "Grouper Category")
                self.assertContains(response, random_content[language])


class SimpleGrouperChangeListTestCase(SimpleSetupMixin, CMSTestCase):
    def test_mixed_change_form(self):
        """Change form contains input for both grouper and content objects"""
        # Arrange
        random_content = self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(f"{self.change_url}?language=en", follow=True)
            # Assert
            # Contains relation to grouper as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__simple_grouper_model"',
            )
            # Contains grouper field with category (and its value)
            self.assertContains(
                response,
                '<input type="text" name="category_name" value="Grouper Category"',
            )
            # Contains content secret message as textarea
            self.assertContains(response, '<textarea name="content__secret_greeting"')
            self.assertContains(response, random_content.secret_greeting)

    def test_empty_content(self) -> None:
        """Without any content being created the changelist shows an empty content text"""
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(self.changelist_url)
            # Assert
            self.assertContains(response, "Empty content")

    def test_with_content(self) -> None:
        """Create one content object and see if it appears in the admin"""
        # Arrange
        random_content = self.createContentInstance()
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(self.changelist_url)
            # Assert
            self.assertContains(response, "Grouper Category")
            self.assertContains(response, random_content.secret_greeting)


class GrouperChangeTestCase(SetupMixin, CMSTestCase):
    def test_mixed_change_form(self):
        """Change form contains input for both grouper and content objects"""
        # Arrange
        random_content = self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(f"{self.change_url}?language=en", follow=True)
            # Assert
            # Contains relation to grouper as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__grouper_model"',
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
            self.assertContains(response, random_content.secret_greeting)

    def test_change_form_contains_defaults_for_groupers(self) -> None:
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(self.change_url + "?language=en", follow=True)
            # Assert
            self.assertContains(response, 'name="content__language" value="en"')
            self.assertNotContains(response, 'name="content__language" value="de"')

            # Act
            response = self.client.get(self.change_url + "?language=de")
            # Assert
            self.assertContains(response, 'name="content__language" value="de"')
            self.assertNotContains(response, 'name="content__language" value="en"')

    @wo_content_permission
    def test_change_form_wo_write_permit(self) -> None:
        """If no change permission exists for content mark content fields readonly."""
        # Arrange
        random_content = self.createContentInstance("en")
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.get(self.change_url + "?language=en")
            # Assert
            # Contains relation to grouper as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__grouper_model"',
            )
            # Contains extra grouping field as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__language" value="en" id="id_content__language">',
            )
            # Contains extra grouping field as hidden input
            self.assertContains(
                response,
                '<input type="hidden" name="content__language" value="en" id="id_content__language">',
            )
            # Contains grouper field with category (and its value)
            self.assertContains(response, '<input type="text" name="category_name" value="Grouper Category"')
            # Does not contain content secret message as textarea
            self.assertContains(response, 'field-content__secret_greeting"')

            self.assertContains(response, random_content.secret_greeting)

    def test_admin_with_write_permit(self) -> None:
        """If change permissions exist for content model its fields in the admin are not readonly."""
        # Assert
        self.assertNotIn("content__secret_greeting", self.admin.get_readonly_fields(None))

    @wo_content_permission
    def test_admin_wo_write_permit(self) -> None:
        # Assert
        self.assertIn("content__secret_greeting", self.admin.get_readonly_fields(None))

    def test_save_grouper_model(self) -> None:
        # Arrange
        random_content = self.createContentInstance("en")
        data = {
            "content__language": "en",
            "category_name": "Changed content",
            "content__region": "world",
            "content__secret_greeting": random_content.secret_greeting,
        }
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.post(self.change_url + "?language=en", data=data)
            # Assert
            self.grouper_instance.refresh_from_db()
            self.assertEqual(response.status_code, 302)  # Expecting redirect
            self.assertEqual(self.grouper_instance.category_name, data["category_name"])

    def test_save_content_model(self) -> None:
        # Arrange
        self.createContentInstance("en")
        data = {
            "content__language": "en",
            "category_name": self.grouper_instance.category_name,
            "content__region": "world",
            "content__secret_greeting": "New greeting",
        }
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.post(self.change_url + "?language=en", data=data)
            content_instance = GrouperModelContent.objects.filter(language="en").first()
        # Assert
        self.assertEqual(response.status_code, 302)  # Expecting redirect
        self.assertIsNotNone(content_instance)
        self.assertEqual(content_instance.secret_greeting, data["content__secret_greeting"])

    def test_create_grouper_model(self) -> None:
        # Arrange
        data = {
            "content__language": "de",
            "category_name": "My new category",
            "content__region": "world",
            "content__secret_greeting": "Some new content",
        }
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.post(self.add_url + "?language=de", data=data)
            grouper_instance = GrouperModel.objects.filter(category_name=data["category_name"]).first()
            content_instance_en = grouper_instance.groupermodelcontent_set.filter(language="en").first()  # Get English
            content_instance_de = grouper_instance.groupermodelcontent_set.filter(language="de").first()  # Get German

        # Assert
        self.assertEqual(response.status_code, 302)  # Expecting redirect
        self.assertEqual(GrouperModel.objects.all().count(), 2)
        self.assertIsNotNone(grouper_instance)
        self.assertIsNone(content_instance_en)  # Should not exist
        self.assertIsNotNone(content_instance_de)  # Should exist
        self.assertEqual(content_instance_de.secret_greeting, data["content__secret_greeting"])  # Has new content

    def test_create_content_model(self) -> None:
        # Arrange
        random_content = self.createContentInstance("en")
        data = {
            "content__language": "de",
            "category_name": self.grouper_instance.category_name,
            "content__region": "world",
            "content__secret_greeting": "New German content",
        }
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.post(self.change_url + "?language=de", data=data)
            content_instance_en = GrouperModelContent.objects.filter(language="en").first()  # Get English
            content_instance_de = GrouperModelContent.objects.filter(language="de").first()  # New German instance
        # Assert
        self.assertEqual(response.status_code, 302)  # Expecting redirect
        self.assertIsNotNone(content_instance_en)
        self.assertEqual(content_instance_en.secret_greeting, random_content.secret_greeting)  # unchanged
        self.assertIsNotNone(content_instance_de)  # Exists?
        self.assertEqual(content_instance_de.secret_greeting, data["content__secret_greeting"])  # Has new content


class SimpleGrouperChangeTestCase(SimpleSetupMixin, CMSTestCase):
    def test_save_grouper_model(self) -> None:
        # Arrange
        random_content = self.createContentInstance()
        data = {
            "category_name": "Changed content",
            "content__region": "world",
            "content__language": "de",
            "content__secret_greeting": random_content.secret_greeting,
        }
        with self.login_user_context(self.admin_user):
            # Act
            response = self.client.post(self.change_url, data=data)
            # Assert
            self.grouper_instance.refresh_from_db()
            self.assertEqual(response.status_code, 302)  # Expecting redirect
            self.assertEqual(self.grouper_instance.category_name, data["category_name"])

    def test_save_content_model(self) -> None:
        # Arrange
        self.createContentInstance()
        data = {
            "category_name": self.grouper_instance.category_name,
            "content__region": "world",
            "content__language": "de",
            "content__secret_greeting": "New greeting",
        }
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.post(self.change_url, data=data)
            content_instance = SimpleGrouperModelContent.objects.first()
        # Assert
        self.assertEqual(response.status_code, 302)  # Expecting redirect
        self.assertIsNotNone(content_instance)
        self.assertEqual(content_instance.secret_greeting, data["content__secret_greeting"])

    def test_create_grouper_model(self) -> None:
        # Arrange
        data = {
            "category_name": "My new category",
            "content__region": "world",
            "content__language": "de",
            "content__secret_greeting": "Some new content",
        }
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.post(self.add_url, data=data)
            grouper_instance = SimpleGrouperModel.objects.filter(category_name=data["category_name"]).first()
            content_instance = grouper_instance.simplegroupermodelcontent_set.first()  # Get content

        # Assert
        self.assertEqual(response.status_code, 302)  # Expecting redirect
        self.assertEqual(SimpleGrouperModel.objects.all().count(), 2)
        self.assertIsNotNone(grouper_instance)
        self.assertIsNotNone(content_instance)  # Should exist
        self.assertEqual(content_instance.secret_greeting, data["content__secret_greeting"])  # Has new content

    def test_create_content_model(self) -> None:
        # Arrange
        self.createContentInstance()
        data = {
            "category_name": self.grouper_instance.category_name,
            "content__region": "world",
            "content__language": "de",
            "content__secret_greeting": "New content",
        }
        # Act
        with self.login_user_context(self.admin_user):
            response = self.client.post(self.change_url, data=data)
            content_instance = SimpleGrouperModelContent.objects.first()  # Get content
        # Assert
        self.assertEqual(response.status_code, 302)  # Expecting redirect
        self.assertIsNotNone(content_instance)
        self.assertEqual(content_instance.secret_greeting, data["content__secret_greeting"])  # Has new content
