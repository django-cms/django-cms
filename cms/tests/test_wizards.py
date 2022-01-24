
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.template import TemplateSyntaxError
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from cms.api import create_page, publish_page
from cms.cms_wizards import CMSPageWizard
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.forms.wizards import CreateCMSPageForm, CreateCMSSubPageForm
from cms.models import Page, PageType, UserSettings
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase
from cms.utils import get_current_site
from cms.utils.conf import get_cms_setting
from cms.wizards.forms import WizardStep2BaseForm, step2_form_factory
from cms.wizards.wizard_base import Wizard
from cms.wizards.wizard_pool import AlreadyRegisteredException, wizard_pool

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
                self.fail("Sequences differ at index {0}".format(idx))

    @classmethod
    def setUpClass(cls):
        super(WizardTestMixin, cls).setUpClass()
        # This prevents auto-discovery, which would otherwise occur as soon as
        # tests start, creating unexpected starting conditions.
        wizard_pool._discovered = True

        class PageWizard(Wizard):
            pass

        # This is a basic Wizard
        cls.page_wizard = PageWizard(
            title=_(u"Page"),
            weight=100,
            form=WizardForm,
            model=Page,
            template_name='my_template.html',  # This doesn't exist anywhere
        )

        class SettingsWizard(Wizard):
            pass

        # This is a Wizard that uses a ModelForm to define the model
        cls.user_settings_wizard = SettingsWizard(
            title=_(u"UserSettings"),
            weight=200,
            form=ModelWizardForm,
        )

        class TitleWizard(Wizard):
            pass

        # This is a bad wizard definition as it neither defines a model, nor
        # uses a ModelForm that has model defined in Meta
        cls.title_wizard = TitleWizard(
            title=_(u"Page"),
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
            published=False
        )
        url = "{0}?edit".format(page.get_absolute_url(language="en"))
        self.assertEqual(self.page_wizard.get_success_url(
            page, language="en"), url)

        # Now again without a language code
        url = "{0}?edit".format(page.get_absolute_url())
        self.assertEqual(self.page_wizard.get_success_url(page), url)

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

    def test_discover(self):
        wizard_pool._reset()
        self.assertFalse(wizard_pool._discovered)
        self.assertEqual(len(wizard_pool._entries), 0)
        wizard_pool._discover()
        self.assertTrue(wizard_pool._discovered)

    def test_register_unregister_isregistered(self):
        wizard_pool._clear()
        self.assertEqual(len(wizard_pool._entries), 0)
        wizard_pool.register(self.page_wizard)
        # Now, try to register the same thing
        with self.assertRaises(AlreadyRegisteredException):
            wizard_pool.register(self.page_wizard)

        self.assertEqual(len(wizard_pool._entries), 1)
        self.assertTrue(wizard_pool.is_registered(self.page_wizard))
        self.assertTrue(wizard_pool.unregister(self.page_wizard))
        self.assertEqual(len(wizard_pool._entries), 0)

        # Now, try to unregister something that is not registered
        self.assertFalse(wizard_pool.unregister(self.user_settings_wizard))

    def test_get_entry(self):
        wizard_pool._clear()
        wizard_pool.register(self.page_wizard)
        entry = wizard_pool.get_entry(self.page_wizard)
        self.assertEqual(entry, self.page_wizard)

    def test_get_entries(self):
        """
        Test that the registered entries are returned in weight-order, no matter
        which order they were added.
        """
        wizard_pool._clear()
        wizard_pool.register(self.page_wizard)
        wizard_pool.register(self.user_settings_wizard)
        wizards = [self.page_wizard, self.user_settings_wizard]
        wizards = sorted(wizards, key=lambda e: getattr(e, 'weight'))
        entries = wizard_pool.get_entries()
        self.assertSequencesEqual(entries, wizards)

        wizard_pool._clear()
        wizard_pool.register(self.user_settings_wizard)
        wizard_pool.register(self.page_wizard)
        wizards = [self.page_wizard, self.user_settings_wizard]
        wizards = sorted(wizards, key=lambda e: getattr(e, 'weight'))
        entries = wizard_pool.get_entries()
        self.assertSequencesEqual(entries, wizards)


class TestPageWizard(WizardTestMixin, CMSTestCase):

    def test_str(self):
        page_wizard = [
            entry for entry in wizard_pool.get_entries()
            if isinstance(entry, CMSPageWizard)
        ][0]
        self.assertEqual(str(page_wizard), page_wizard.title)

    def test_repr(self):
        page_wizard = [
            entry for entry in wizard_pool.get_entries()
            if isinstance(entry, CMSPageWizard)
        ][0]
        self.assertIn("cms.cms_wizards.CMSPageWizard", repr(page_wizard))
        self.assertIn("id={}".format(page_wizard.id), repr(page_wizard))
        self.assertIn(hex(id(page_wizard)), repr(page_wizard))

    def test_wizard_first_page_published(self):
        superuser = self.get_superuser()
        data = {
            'title': 'page 1',
            'slug': 'page_1',
            'page_type': None,
        }
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        page = form.save()

        self.assertTrue(page.is_published('en'))

        with self.login_user_context(superuser):
            url = page.get_absolute_url('en')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_wizard_create_child_page(self):
        superuser = self.get_superuser()
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
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        child_page = form.save()

        self.assertEqual(child_page.node.depth, 2)
        self.assertEqual(child_page.parent_page, parent_page)
        self.assertEqual(child_page.get_title('en'), 'Child')
        self.assertEqual(child_page.get_path('en'), 'parent/child')

    def test_wizard_create_child_page_under_page_type(self):
        """
        When a user creates a child page through the wizard,
        if the parent page is a page-type, the child page should
        also be a page-type.
        """
        site = get_current_site()
        superuser = self.get_superuser()
        source_page = create_page(
            title="Source",
            template=TEMPLATE_INHERITANCE_MAGIC,
            language="en",
        )

        with self.login_user_context(superuser):
            self.client.post(
                self.get_admin_url(PageType, 'add'),
                data={'source': source_page.pk, 'title': 'type1', 'slug': 'type1', '_save': 1},
            )

        types_root = PageType.get_root_page(site)
        parent_page = types_root.get_child_pages()[0]
        data = {
            'title': 'page-type-child',
            'slug': 'page-type-child',
            'page_type': None,
        }
        form = CreateCMSSubPageForm(
            data=data,
            wizard_page=parent_page,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())

        child_page = form.save()

        self.assertTrue(child_page.is_page_type)
        self.assertFalse(child_page.in_navigation)
        self.assertEqual(child_page.node.depth, 3)
        self.assertEqual(child_page.parent_page, parent_page)
        self.assertEqual(child_page.get_title('en'), 'page-type-child')
        self.assertEqual(child_page.get_path('en'), 'page_types/type1/page-type-child')

    def test_wizard_create_atomic(self):
        # Ref: https://github.com/divio/django-cms/issues/5652
        # We'll simulate a scenario where a user creates a page with an
        # invalid template which causes Django to throw an error when the
        # template is scanned for placeholders and thus short circuits the
        # creation mechanism.
        superuser = self.get_superuser()
        data = {
            'title': 'page 1',
            'slug': 'page_1',
            'page_type': None,
        }
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )

        self.assertTrue(form.is_valid())
        self.assertFalse(Page.objects.filter(template=TEMPLATE_INHERITANCE_MAGIC).exists())

        with self.settings(CMS_TEMPLATES=[("col_invalid.html", "notvalid")]):
            self.assertRaises(TemplateSyntaxError, form.save)
            # The template raised an exception which should cause the database to roll back
            # instead of committing a page in a partial state.
            self.assertFalse(Page.objects.filter(template=TEMPLATE_INHERITANCE_MAGIC).exists())

    def test_wizard_content_placeholder_setting(self):
        """
        Tests that the PageWizard respects the
        CMS_PAGE_WIZARD_CONTENT_PLACEHOLDER setting.
        """
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
            superuser = self.get_superuser()
            page = create_page("wizard home", "page_wizard.html", "en")
            publish_page(page, superuser, "en")
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
                wizard_user=superuser,
                wizard_language='en',
            )
            self.assertTrue(form.is_valid())
            page = form.save()
            page.publish('en')

            with self.login_user_context(superuser):
                url = page.get_absolute_url('en')
                expected = '<div class="sub-content">{0}</div>'.format(content)
                unexpected = '<div class="content">{0}</div>'.format(content)
                response = self.client.get(url)
                self.assertContains(response, expected, status_code=200)
                self.assertNotContains(response, unexpected, status_code=200)

    def test_wizard_content_placeholder_bad_setting(self):
        """
        Tests that the PageWizard won't respect a 'bad' setting such as
        targeting a static-placeholder. In this case, will just fail to
        add the content (without error).
        """
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
            superuser = self.get_superuser()
            page = create_page("wizard home", "page_wizard.html", "en")
            publish_page(page, superuser, "en")
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
                wizard_user=superuser,
                wizard_language='en',
            )
            self.assertTrue(form.is_valid())
            page = form.save()
            page.publish('en')

            with self.login_user_context(superuser):
                url = page.get_absolute_url('en')
                response = self.client.get(url)
                self.assertNotContains(response, content, status_code=200)

    def test_create_page_with_empty_fields(self):
        superuser = self.get_superuser()
        data = {
            'title': '',
            'slug': '',
            'page_type': None,
        }
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertFalse(form.is_valid())

    def test_create_page_with_existing_slug(self):
        superuser = self.get_superuser()
        data = {
            'title': 'page',
            'slug': 'page',
            'page_type': None,
        }
        create_page(
            'page',
            'nav_playground.html',
            language='en',
            published=True,
            slug='page'
        )

        # slug -> page-1
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().title_set.filter(slug='page-2'))

        # slug -> page-2
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().title_set.filter(slug='page-3'))

        # Now explicitly request the page-2 slug
        data['slug'] = 'page-2'

        # slug -> page-2-2
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().title_set.filter(slug='page-2-2'))

        # slug -> page-2-3
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save().title_set.filter(slug='page-2-3'))
