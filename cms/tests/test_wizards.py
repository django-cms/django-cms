# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.template import TemplateSyntaxError
from django.test.utils import override_settings
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _

from cms.api import create_page, publish_page
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.forms.wizards import CreateCMSPageForm
from cms.models import Page, UserSettings
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase
from cms.utils.conf import get_cms_setting
from cms.wizards.wizard_base import Wizard
from cms.wizards.wizard_pool import wizard_pool, AlreadyRegisteredException


class WizardForm(forms.Form):
    pass


class ModelWizardForm(ModelForm):
    class Meta:
        model = UserSettings
        exclude = []


class BadModelForm(ModelForm):
    class Meta:
        pass


class WizardTestMixin(object):
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

    def test_str(self):
        self.assertEqual(str(self.page_wizard), self.page_wizard.title)

    def test_repr(self):
        self.assertEqual(self.page_wizard.__repr__(), 'Wizard: "Page"')

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
            created_by=smart_text(user),
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

    def test_wizard_first_page_published(self):
        superuser = self.get_superuser()
        data = {
            'title': 'page 1',
            'slug': 'page_1',
            'page_type': None,
        }
        form = CreateCMSPageForm(data=data)
        form.page = None
        form.language_code = 'en'
        form.user = superuser
        self.assertTrue(form.is_valid())
        page = form.save()

        self.assertTrue(page.is_published('en'))

        with self.login_user_context(superuser):
            url = page.get_absolute_url('en')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

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
        form = CreateCMSPageForm(data=data)
        form.page = None
        form.language_code = 'en'
        form.user = superuser

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
            form = CreateCMSPageForm(data=data)
            form.page = page
            form.language_code = 'en'
            form.user = superuser
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
            form = CreateCMSPageForm(data=data)
            form.page = page
            form.language_code = 'en'
            form.user = superuser
            self.assertTrue(form.is_valid())
            page = form.save()
            page.publish('en')

            with self.login_user_context(superuser):
                url = page.get_absolute_url('en')
                response = self.client.get(url)
                self.assertNotContains(response, content, status_code=200)


# This entire test class can be removed in 3.5.0
class TestWizardSettings(CMSTestCase):
    def test_old_wizard_setting(self):
        value = 'obscure-named-placeholder'
        with override_settings(CMS_WIZARD_CONTENT_PLACEHOLDER=value):
            self.assertEqual(get_cms_setting('PAGE_WIZARD_CONTENT_PLACEHOLDER'), value)

    def test_new_wizard_setting(self):
        value = 'obscure-named-placeholder'
        with override_settings(CMS_PAGE_WIZARD_CONTENT_PLACEHOLDER=value):
            self.assertEqual(get_cms_setting('PAGE_WIZARD_CONTENT_PLACEHOLDER'), value)

    def test_new_wizard_setting_are_preferred(self):
        old_value = 'obscure-named-placeholder-old'
        new_value = 'obscure-named-placeholder-new'
        with override_settings(CMS_WIZARD_CONTENT_PLACEHOLDER=old_value,
                               CMS_PAGE_WIZARD_CONTENT_PLACEHOLDER=new_value):
            self.assertEqual(get_cms_setting('PAGE_WIZARD_CONTENT_PLACEHOLDER'), new_value)
