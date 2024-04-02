from unittest.mock import Mock, patch

from django import forms
from django.apps import apps
from django.apps.registry import Apps
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.template import TemplateSyntaxError
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from cms import app_registration
from cms.api import create_page
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.forms.wizards import CreateCMSPageForm, CreateCMSSubPageForm
from cms.models import Page, UserSettings
from cms.test_utils.project.backwards_wizards.wizards import wizard
from cms.test_utils.project.sampleapp.cms_wizards import sample_wizard
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase
from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_preview_url,
)
from cms.utils import get_current_site
from cms.utils.conf import get_cms_setting
from cms.utils.setup import setup_cms_apps
from cms.wizards.forms import WizardStep2BaseForm, step2_form_factory
from cms.wizards.helpers import get_entries, get_entry
from cms.wizards.wizard_base import Wizard
from cms.wizards.wizard_pool import (
    AlreadyRegisteredException,
    entry_choices,
    wizard_pool,
)

CreateCMSPageForm = step2_form_factory(
    mixin_cls=WizardStep2BaseForm,
    entry_form_class=CreateCMSPageForm,
)

CreateCMSSubPageForm = step2_form_factory(
    mixin_cls=WizardStep2BaseForm,
    entry_form_class=CreateCMSSubPageForm,
)


class WizardForm(forms.Form):
    pass


class ModelWizardForm(ModelForm):
    class Meta:
        model = UserSettings
        exclude = []


class BadModelForm(ModelForm):
    class Meta:
        pass


class WizardTestMixin:
    page_wizard = None
    title_wizard = None

    def assertSequencesEqual(self, seq_a, seq_b):
        seq_a = list(seq_a)
        seq_b = list(seq_b)
        zipped = list(zip(seq_a, seq_b))
        if len(zipped) < len(seq_a) or len(zipped) < len(seq_b):
            self.fail("Sequence lengths are not the same.")
        for idx, (a, b) in enumerate(zipped):
            if a != b:
                self.fail(f"Sequences differ at index {idx}")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # This prevents auto-discovery, which would otherwise occur as soon as
        # tests start, creating unexpected starting conditions.
        wizard_pool._discovered = True

        class PageWizard(Wizard):
            pass

        # This is a basic Wizard
        cls.page_wizard = PageWizard(
            title=_("Page"),
            weight=100,
            form=WizardForm,
            model=Page,
            template_name='my_template.html',  # This doesn't exist anywhere
        )

        class SettingsWizard(Wizard):
            pass

        # This is a Wizard that uses a ModelForm to define the model
        cls.user_settings_wizard = SettingsWizard(
            title=_("UserSettings"),
            weight=200,
            form=ModelWizardForm,
        )

        class PageContentWizard(Wizard):
            pass

        # This is a bad wizard definition as it neither defines a model, nor
        # uses a ModelForm that has model defined in Meta
        cls.title_wizard = PageContentWizard(
            title=_("Page"),
            weight=100,
            form=BadModelForm,
            template_name='my_template.html',  # This doesn't exist anywhere
        )


class TestWizardBase(WizardTestMixin, TransactionCMSTestCase):

    def test_user_has_add_permission(self):
        # Test does not have permission
        user = self.get_staff_user_with_no_permissions()
        self.assertFalse(self.page_wizard.user_has_add_permission(user))

        # Test has permission
        user = self.get_superuser()
        self.assertTrue(self.page_wizard.user_has_add_permission(user))

    def test_get_success_url(self):
        user = self.get_superuser()
        page = create_page(
            title="Sample Page",
            template=TEMPLATE_INHERITANCE_MAGIC,
            language="en",
            created_by=smart_str(user),
            parent=None,
            in_navigation=True,
        )
        url = page.get_absolute_url(language="en")
        self.assertEqual(self.page_wizard.get_success_url(
            page, language="en"), url)

        # Now again without a language code
        url = page.get_absolute_url()
        self.assertEqual(self.page_wizard.get_success_url(page), url)

    def test_get_edit_url(self):
        user = self.get_superuser()
        page = create_page(
            title="Sample Page",
            template=TEMPLATE_INHERITANCE_MAGIC,
            language="en",
            created_by=smart_str(user),
            parent=None,
            in_navigation=True,
        )

        extension = apps.get_app_config('cms').cms_extension

        with patch.object(extension, 'toolbar_enabled_models', {Page: page}):
            url = self.page_wizard.get_success_url(
                page, language="en")
            self.assertEqual(
                url, get_object_edit_url(page, language="en"))

    def test_get_preview_url(self):
        wizard_preview_mode = Wizard(
            title=_("Page"),
            weight=100,
            form=WizardForm,
            model=Page,
            template_name='my_template.html',  # This doesn't exist anywhere
            edit_mode_on_success=False
        )

        user = self.get_superuser()
        page = create_page(
            title="Sample Page",
            template=TEMPLATE_INHERITANCE_MAGIC,
            language="en",
            created_by=smart_str(user),
            parent=None,
            in_navigation=True,
        )

        extension = apps.get_app_config('cms').cms_extension

        with patch.object(extension, 'toolbar_enabled_models', {Page: page}):
            url = wizard_preview_mode.get_success_url(
                page, language="en")
            self.assertEqual(
                url, get_object_preview_url(page, language="en"))

    def test_get_model(self):
        self.assertEqual(self.page_wizard.get_model(), Page)
        self.assertEqual(self.user_settings_wizard.get_model(), UserSettings)
        with self.assertRaises(ImproperlyConfigured):
            self.title_wizard.get_model()

    def test_endpoint_auth_required(self):
        endpoint = reverse('cms_wizard_create')
        staff_active = self._create_user("staff-active", is_staff=True, is_superuser=False, is_active=True)

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 403)

        with self.login_user_context(staff_active):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)


class TestWizardPool(WizardTestMixin, CMSTestCase):

    def tearDown(self):
        # Clean up in case anything has been removed or added to the
        # registered wizards, so other tests don't have problems
        extension = apps.get_app_config('cms').cms_extension
        extension.wizards = {}
        configs_with_wizards = [
            app.cms_config for app in app_registration.get_cms_config_apps()
            if hasattr(app.cms_config, 'cms_wizards')
        ]
        for config in configs_with_wizards:
            extension.configure_wizards(config)
        # Clean up in case cached apps are different than the defaults
        app_registration.get_cms_extension_apps.cache_clear()
        app_registration.get_cms_config_apps.cache_clear()

    def test_is_registered_for_registered_wizard(self):
        """
        Test for backwards compatibility of is_registered when checking
        a registered wizard.
        """
        is_registered = wizard_pool.is_registered(cms_page_wizard)
        self.assertTrue(is_registered)

    def test_is_registered_for_unregistered_wizard(self):
        """
        Test for backwards compatibility of is_registered when checking
        an unregistered wizard.
        """
        is_registered = wizard_pool.is_registered(self.page_wizard)
        self.assertFalse(is_registered)

    def test_unregister_registered_wizard(self):
        """
        Test for backwards compatibility of the unregister method.
        Removes a wizard from the wizards dict.
        """
        was_unregistered = wizard_pool.unregister(cms_page_wizard)
        registered_wizards = apps.get_app_config('cms').cms_extension.wizards
        self.assertNotIn(cms_page_wizard.id, registered_wizards)
        self.assertTrue(was_unregistered)

    def test_unregister_unregistered_wizard(self):
        """
        Test for backwards compatibility of the unregister method.
        Returns False if wizard not found.
        """
        was_unregistered = wizard_pool.unregister(self.page_wizard)
        self.assertFalse(was_unregistered)

    def test_register_already_registered_wizard(self):
        """
        Test for backwards compatibility of the register method.
        Raises AlreadyRegisteredException if the wizard is already
        registered.
        """
        with self.assertRaises(AlreadyRegisteredException):
            wizard_pool.register(cms_page_wizard)

    def test_register_unregistered_wizard(self):
        """
        Test for backwards compatibility of the register method.
        Adds the wizard to the wizards dict.
        """
        wizard_pool.register(self.page_wizard)
        registered_wizards = apps.get_app_config('cms').cms_extension.wizards
        self.assertIn(self.page_wizard.id, registered_wizards)

    @patch('cms.wizards.wizard_pool.get_entry')
    def test_get_entry(self, mocked_get_entry):
        """
        Test for backwards compatibility of wizard_pool.get_entry.
        Checking we use the new get_entry under the hood.
        """
        wizard_pool.get_entry(cms_page_wizard)
        mocked_get_entry.assert_called_once()

    def test_old_registration_still_works(self):
        """
        Integration-like test checking that if you register your wizard
        by adding wizard_pool.register(wizard) to cms_wizards.py it will
        correctly register the wizard. This ensures backwards
        compatibility.
        """
        # NOTE: Because of how the override_settings decorator works,
        # we can't use it for this test as the app registry first
        # gets loaded with the default apps and then again with
        # the overridden ones.
        INSTALLED_APPS = [
            'cms',
            'treebeard',
            'cms.test_utils.project.backwards_wizards',
        ]
        mocked_apps = Apps(installed_apps=INSTALLED_APPS)
        # clear out app registration cache now that installed apps have
        # changed
        app_registration.get_cms_extension_apps.cache_clear()
        app_registration.get_cms_config_apps.cache_clear()
        # Run the setup with the mocked installed apps. Due to the order
        # of imports and other fun things, apps have to be patched
        # in multiple places. If functions are moved around the code
        # this could get worse.
        with patch('cms.app_registration.apps', mocked_apps):
            with patch('cms.wizards.wizard_pool.apps', mocked_apps):
                setup_cms_apps()
        # Check the wizards built into the cms app and the wizard from
        # the backwards_wizards app have been picked up.
        # The backwards_wizards app does not have a cms_config.py but
        # registers its wizard by adding wizard_pool.register(wizard)
        # to cms_wizards.py which is the old way we want backwards
        # compatibility with.
        cms_app = mocked_apps.get_app_config('cms')
        expected_wizards = {
            cms_page_wizard.id: cms_page_wizard,
            cms_subpage_wizard.id: cms_subpage_wizard,
            wizard.id: wizard,
        }
        self.assertDictEqual(cms_app.cms_extension.wizards, expected_wizards)


class TestPageWizard(WizardTestMixin, CMSTestCase):

    def test_str(self):
        self.assertEqual(str(cms_page_wizard), cms_page_wizard.title)

    def test_repr(self):
        self.assertIn("cms.cms_wizards.CMSPageWizard", repr(cms_page_wizard))
        self.assertIn(f"id={cms_page_wizard.id}", repr(cms_page_wizard))
        self.assertIn(hex(id(cms_page_wizard)), repr(cms_page_wizard))

    def test_wizard_create_child_page(self):
        site = get_current_site()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            request = self.get_request()
        parent_page = create_page(
            title="Parent",
            template=TEMPLATE_INHERITANCE_MAGIC,
            language="en",
        )
        data = {
            'title': 'Child',
            'slug': 'child',
            'page_type': None,
        }
        form = CreateCMSSubPageForm(
            data=data,
            wizard_page=parent_page,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )
        self.assertTrue(form.is_valid())
        child_page = form.save()

        self.assertEqual(child_page.node.depth, 2)
        self.assertEqual(child_page.parent_page, parent_page)
        self.assertEqual(child_page.get_title('en'), 'Child')
        self.assertEqual(child_page.get_path('en'), 'parent/child')

    def test_wizard_create_atomic(self):
        # Ref: https://github.com/divio/django-cms/issues/5652
        # We'll simulate a scenario where a user creates a page with an
        # invalid template which causes Django to throw an error when the
        # template is scanned for placeholders and thus short circuits the
        # creation mechanism.
        site = get_current_site()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            request = self.get_request()
        data = {
            'title': 'page 1',
            'slug': 'page_1',
            'page_type': None,
        }
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )

        self.assertTrue(form.is_valid())
        self.assertFalse(Page.objects.filter(pagecontent_set__template=TEMPLATE_INHERITANCE_MAGIC).exists())

        with self.settings(CMS_TEMPLATES=[("col_invalid.html", "notvalid")]):
            self.assertRaises(TemplateSyntaxError, form.save)
            # The template raised an exception which should cause the database to roll back
            # instead of committing a page in a partial state.
            self.assertFalse(Page.objects.filter(pagecontent_set__template=TEMPLATE_INHERITANCE_MAGIC).exists())

    def test_wizard_content_placeholder_setting(self):
        """
        Tests that the PageWizard respects the
        CMS_PAGE_WIZARD_CONTENT_PLACEHOLDER setting.
        """
        site = get_current_site()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            request = self.get_request()
        templates = get_cms_setting('TEMPLATES')
        # NOTE, there are 4 placeholders on this template, defined in this
        # order: 'header', 'content', 'sub-content', 'footer'.
        # 'footer' is a static-placeholder.
        templates.append(('page_wizard.html', 'page_wizard.html', ))

        settings = {
            'CMS_TEMPLATES': templates,
            'CMS_PAGE_WIZARD_DEFAULT_TEMPLATE': 'page_wizard.html',
            'CMS_PAGE_WIZARD_CONTENT_PLACEHOLDER': 'sub-content',
        }

        with override_settings(**settings):
            page = create_page("wizard home", "page_wizard.html", "en")
            content = '<p>sub-content content.</p>'
            data = {
                'title': 'page 1',
                'slug': 'page_1',
                'page_type': None,
                'content': content,
            }
            form = CreateCMSPageForm(
                data=data,
                wizard_page=page,
                wizard_site=site,
                wizard_language='en',
                wizard_request=request,
            )
            self.assertTrue(form.is_valid())
            page = form.save()

            with self.login_user_context(superuser):
                url = page.get_absolute_url('en')
                expected = f'<div class="sub-content">{content}</div>'
                unexpected = f'<div class="content">{content}</div>'
                response = self.client.get(url)
                self.assertContains(response, expected, status_code=200)
                self.assertNotContains(response, unexpected, status_code=200)

    def test_wizard_content_placeholder_bad_setting(self):
        """
        Tests that the PageWizard won't respect a 'bad' setting such as
        targeting a static-placeholder. In this case, will just fail to
        add the content (without error).
        """
        site = get_current_site()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            request = self.get_request()
        templates = get_cms_setting('TEMPLATES')
        # NOTE, there are 4 placeholders on this template, defined in this
        # order: 'header', 'content', 'sub-content', 'footer'.
        # 'footer' is a static-placeholder.
        templates.append(('page_wizard.html', 'page_wizard.html', ))

        settings = {
            'CMS_TEMPLATES': templates,
            'CMS_PAGE_WIZARD_DEFAULT_TEMPLATE': 'page_wizard.html',
            # This is a bad setting.
            'CMS_PAGE_WIZARD_CONTENT_PLACEHOLDER': 'footer',
        }

        with override_settings(**settings):
            page = create_page("wizard home", "page_wizard.html", "en")
            content = '<p>footer content.</p>'
            data = {
                'title': 'page 1',
                'slug': 'page_1',
                'page_type': None,
                'content': content,
            }
            form = CreateCMSPageForm(
                data=data,
                wizard_page=page,
                wizard_site=site,
                wizard_language='en',
                wizard_request=request,
            )
            self.assertTrue(form.is_valid())
            page = form.save()

            with self.login_user_context(superuser):
                url = page.get_absolute_url('en')
                response = self.client.get(url)
                self.assertNotContains(response, content, status_code=200)

    def test_create_page_with_empty_fields(self):
        site = get_current_site()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            request = self.get_request()
        data = {
            'title': '',
            'slug': '',
            'page_type': None,
        }
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )
        self.assertFalse(form.is_valid())

    def test_create_page_with_existing_slug(self):
        site = get_current_site()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            request = self.get_request()
        data = {
            'title': 'page',
            'slug': 'page',
            'page_type': None,
        }
        create_page(
            'page',
            'nav_playground.html',
            language='en',
            slug='page'
        )

        # slug -> page-1
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().get_urls().filter(slug='page-2'))

        # slug -> page-2
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().get_urls().filter(slug='page-3'))

        # Now explicitly request the page-2 slug
        data['slug'] = 'page-2'

        # slug -> page-2-2
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().get_urls().filter(slug='page-2-2'))

        # slug -> page-2-3
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_site=site,
            wizard_language='en',
            wizard_request=request,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().get_urls().filter(slug='page-2-3'))


class TestWizardHelpers(CMSTestCase):

    def setUp(self):
        # The results of get_cms_extension_apps and get_cms_config_apps
        # are cached. Clear this cache because installed apps change
        # between tests and therefore unlike in a live environment,
        # results of this function can change between tests
        app_registration.get_cms_extension_apps.cache_clear()
        app_registration.get_cms_config_apps.cache_clear()

    def test_get_entries_orders_by_weight(self):
        """
        The get_entries function returns the registered wizards
        ordered by weight.
        """
        # The test setup registers two wizards from cms itself
        # (cms_page_wizard and cms_subpage_wizard) and one from
        # test_utils.project.sampleapp (sample_wizard)
        # We know these are definitely being ordered by weight if
        # sample_wizard is in the middle because app registration
        # would first add the wizards from cms to a list and then add
        # those from sampleapp, so the sampleapp wizard could not
        # be in the middle by default
        expected = [cms_page_wizard, sample_wizard, cms_subpage_wizard]
        entries = get_entries()
        self.assertListEqual(entries, expected)

    def test_get_entry_returns_wizard_by_id(self):
        """
        The get_entry function returns the wizard when a wizard id is
        supplied.
        """
        entry = get_entry(sample_wizard.id)
        self.assertEqual(entry, sample_wizard)


class TestEntryChoices(CMSTestCase):

    def test_generates_choices_in_weighted_order(self):
        """
        The entry_choices function returns the wizards ordered by weight
        """
        user = self.get_superuser()
        page = create_page('home', 'nav_playground.html', 'en')
        wizard_choices = [option for option in entry_choices(user, page)]
        expected = [
            (cms_page_wizard.id, cms_page_wizard.title),
            (sample_wizard.id, sample_wizard.title),
            (cms_subpage_wizard.id, cms_subpage_wizard.title),
        ]
        self.assertListEqual(wizard_choices, expected)

    @patch.object(
        cms_page_wizard, 'user_has_add_permission',
        Mock(return_value=False)
    )
    def test_doesnt_generate_choice_if_user_doesnt_have_permission(self):
        """
        The entry_choices function only returns the wizards that the
        user has permissions for
        """
        user = self.get_superuser()
        page = create_page('home', 'nav_playground.html', 'en')
        wizard_choices = [option for option in entry_choices(user, page)]
        expected = [
            # Missing cms_page_wizard entry
            (sample_wizard.id, sample_wizard.title),
            (cms_subpage_wizard.id, cms_subpage_wizard.title),
        ]
        self.assertListEqual(wizard_choices, expected)
