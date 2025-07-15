import copy

from django.contrib.admin import site
from django.templatetags.static import static
from django.utils.crypto import get_random_string
from django.utils.translation import get_language, override as force_language

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
        self.grouper_instance = GrouperModel.objects.create(category_name="Grouper Category")
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
        self.grouper_instance = SimpleGrouperModel.objects.create(category_name="Grouper Category")
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

    def createContentInstance(self, language="en", grouper_instance=None, secret_greeting=None):
        """Creates a content instance with a random content for a language. The random content is returned
        to be able to check if it appears in forms etc."""

        assert language == "en", "Only English is supported for SimpleGrouperModelContent"
        grouper_instance = grouper_instance or self.grouper_instance
        secret_greeting = secret_greeting or get_random_string(16)
        instance = SimpleGrouperModelContent.objects.create(
            simple_grouper_model=grouper_instance,
            secret_greeting=secret_greeting,
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
            self.assertContains(
                response, f'href="/en/admin/sampleapp/{self.groupermodel}/{self.grouper_instance.pk}/change/?'
            )
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
            self.assertContains(
                response, f'href="/en/admin/sampleapp/{self.groupermodel}/{self.grouper_instance.pk}/change/?'
            )
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

    def test_extra_grouping_field_fixed(self):
        """Extra grouping fields are retrieved correctly"""
        with force_language("en"):
            expected_language = "zh"
            self.admin.language = expected_language

            admin_language = self.admin.get_language()
            current_content_filters = self.admin.current_content_filters

            self.assertEqual(admin_language, expected_language)
            self.assertEqual(current_content_filters["language"], expected_language)

    def test_extra_grouping_field_current(self):
        """Extra grouping fields (language) when not set return current default correctly"""
        del self.admin.language  # No pre-set language
        expected_language = get_language()

        admin_language = self.admin.get_language()
        current_content_filters = self.admin.current_content_filters

        self.assertEqual(admin_language, expected_language)
        self.assertEqual(current_content_filters["language"], expected_language)

    def test_prepopulated_fields_pass_checks(self):
        """Prepopulated fields work for content field"""
        # Arrange
        admin = copy.copy(self.admin)
        admin.prepopulated_fields = dict(
            category_name=["category_name"],  # Both key and value from GrouperModel
            some_field=["content__secret_greeting"],  # Value from ContentModel
            content__secret_greeting=["category_name"],  # Key from GrouperModel
            content__region=["content__secret_greeting"],  # Both key and value from ContentModel
        )

        # Act
        check_results = admin.check()

        # Assert
        self.assertEqual(check_results, [])  # No errors

    def test_invalid_prepopulated_content_fields_fail_checks(self):
        """Prepopulated fields with invalid content field names fail checks"""
        # Arrange
        admin = copy.copy(self.admin)
        admin.prepopulated_fields = dict(
            some_field=["content__public_greeting"],  # Value from ContentModel: 1 error
            content__public_greeting=["category_name"],  # Key from GrouperModel: 1 error
            content__country=["content__public_greeting"],  # Both key and value from ContentModel: 2 errors
        )

        # Act
        check_results = admin.check()

        # Assert
        self.assertEqual(len(check_results), 4)  # No errors


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
            "some_field": "some content",
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
            "some_field": "some content",
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
            "some_field": "some content",
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
            "some_field": "some content",
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


class GrouperSearchTestCase(SimpleSetupMixin, CMSTestCase):
    """Test suite for Grouper model search functionality in Django admin."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SEARCH_FIELDS_DEFAULT = ("category_name", "content__secret_greeting")
        cls.SEARCH_FIELDS_GROUPER_ONLY = ("category_name",)
        cls.SEARCH_FIELDS_STARTSWITH = ("^category_name", "^content__secret_greeting")
        cls.SEARCH_FIELDS_EXACT = ("=category_name", "=content__secret_greeting")

    def setUp(self) -> None:
        super().setUp()
        self._setup_test_data()
        self._setup_admin_config()

    def _setup_test_data(self):
        """Create test instances and content objects."""
        self.another_grouper_instance = SimpleGrouperModel.objects.create(category_name="Another_Category")
        self.grouper_content_objects = {}

        for grouper in [self.grouper_instance, self.another_grouper_instance]:
            self.grouper_content_objects[grouper.id] = self.createContentInstance(
                language="en", grouper_instance=grouper, secret_greeting=f"{grouper.category_name}_Greeting"
            )

    def _setup_admin_config(self):
        """Configure admin search fields."""
        self.admin.search_fields = self.SEARCH_FIELDS_DEFAULT

    def tearDown(self) -> None:
        self.another_grouper_instance.delete()
        super().tearDown()

    def _get_search_url(self, query=""):
        """Helper to construct search URL."""
        return f"{self.changelist_url}?q={query}"

    def _get_admin_change_url(self, instance):
        """Helper to construct admin change URL."""
        return f'href="/en/admin/sampleapp/{self.groupermodel}/{instance.pk}/change/?'

    def _assert_instance_in_response(self, response, instance, should_contain=True):
        """Helper to assert instance presence in response."""
        assertion_method = self.assertContains if should_contain else self.assertNotContains
        assertion_method(response, instance.category_name)
        assertion_method(response, self._get_admin_change_url(instance))

    def _assert_search_results(self, response, expected_instances):
        """Helper to assert multiple search results."""
        all_instances = [self.grouper_instance, self.another_grouper_instance]

        for instance in all_instances:
            should_contain = instance in expected_instances
            self._assert_instance_in_response(response, instance, should_contain)

    def _perform_search(self, query, expected_instances):
        """Helper to perform search and assert results."""
        with self.login_user_context(self.admin_user):
            response = self.client.get(self._get_search_url(query), follow=True)
            self._assert_search_results(response, expected_instances)
            return response

    def _test_expected_result_count(self, query, expected_count):
        with self.login_user_context(self.admin_user):
            response = self.client.get(self._get_search_url(query), follow=True)
            content = response.content.decode()
            actual_count = content.count('class="action-checkbox"')
            self.assertEqual(
                actual_count,
                expected_count,
                f"Expected {expected_count} results for query '{query}' "
                f"with search_fields {self.admin.search_fields}, got {actual_count}",
            )

    def test_search_with_empty_query_returns_all_results(self):
        """Empty search query should return all grouper instances."""
        expected_instances = [self.grouper_instance, self.another_grouper_instance]
        self._perform_search("", expected_instances)

    def test_search_by_grouper_category_name(self):
        """Search by grouper's category name should return matching instance."""
        search_token = self.grouper_instance.category_name
        expected_instances = [self.grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_search_by_content_field(self):
        """Search by content field should return matching instance."""
        content_obj = self.grouper_content_objects[self.grouper_instance.id]
        search_token = content_obj.secret_greeting[:5]
        expected_instances = [self.grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_search_with_no_matching_results(self):
        """Search with non-existent term should return no results."""
        search_token = get_random_string(10)
        expected_instances = []
        self._perform_search(search_token, expected_instances)

    def test_search_returns_multiple_results_by_category(self):
        """Search by common category term should return multiple instances."""
        search_token = "Category"
        expected_instances = [self.grouper_instance, self.another_grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_search_returns_multiple_results_by_content(self):
        """Search by common content term should return multiple instances."""
        search_token = "Greeting"
        expected_instances = [self.grouper_instance, self.another_grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_search_without_content_fields_by_category(self):
        """Search should work when content fields are excluded from search_fields."""
        self.admin.search_fields = self.SEARCH_FIELDS_GROUPER_ONLY
        search_token = "Category"
        expected_instances = [self.grouper_instance, self.another_grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_search_without_content_fields_by_content_returns_nothing(self):
        """Search by content should return nothing when content fields excluded."""
        self.admin.search_fields = self.SEARCH_FIELDS_GROUPER_ONLY
        search_token = "Greeting"
        expected_instances = []
        self._perform_search(search_token, expected_instances)

    def test_startswith_search_by_category(self):
        """Test startswith (^) search modifier on category field."""
        self.admin.search_fields = ("^category_name",)
        search_token = "Grouper"  # Matches "Grouper_Category" but not "Another_Category"
        expected_instances = [self.grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_exact_search_by_category(self):
        """Test exact match (=) search modifier on category field."""
        self.admin.search_fields = ("=category_name",)
        search_token = "Another_Category"
        expected_instances = [self.another_grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_startswith_search_by_content(self):
        """Test startswith (^) search modifier on content field."""
        self.admin.search_fields = ("category_name", "^content__secret_greeting")
        content_obj = self.grouper_content_objects[self.another_grouper_instance.id]
        search_token = content_obj.secret_greeting[:-5]  # Partial match from start
        expected_instances = [self.another_grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_exact_search_by_content(self):
        """Test exact match (=) search modifier on content field."""
        self.admin.search_fields = ("category_name", "=content__secret_greeting")
        content_obj = self.grouper_content_objects[self.another_grouper_instance.id]
        search_token = content_obj.secret_greeting  # Exact match
        expected_instances = [self.another_grouper_instance]
        self._perform_search(search_token, expected_instances)

    def test_search_with_multiple_results_and_grouper_query(self):
        """Test search configuration with category_name contains search."""
        query = "Category"
        self.admin.search_fields = ("category_name",)
        self._test_expected_result_count(query, 2)

    def test_search_with_startswith_grouper_query(self):
        """Test search configuration with category_name starts with search."""
        query = "Grouper"
        self.admin.search_fields = ("^category_name",)
        self._test_expected_result_count(query, 1)

    def test_search_configurations_category_name_exact(self):
        """Test search configuration with category_name exact match search."""
        query = "Another_Category"
        self.admin.search_fields = ("=category_name",)
        self._test_expected_result_count(query, 1)

    def test_search_content_secret_greeting_with_multiple_results(self):
        """Test search configuration with content__secret_greeting field search."""
        query = "Greeting"
        self.admin.search_fields = ("content__secret_greeting",)
        self._test_expected_result_count(query, 2)
