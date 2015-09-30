# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext as _
from cms.models import Page, UserSettings
from cms.test_utils.testcases import CMSTestCase
from cms.wizards.wizard_base import Wizard
from cms.wizards.wizard_pool import wizard_pool, AlreadyRegisteredException


class TestPageWizard(Wizard):
    pass

class TestUserSettingsWizard(Wizard):
    pass

class PageWizardForm(forms.Form):
    pass


class TitleWizardForm(forms.Form):
    pass


class WizardTestMixin(object):
    page_wizard = None
    title_wizard = None

    @classmethod
    def setUpClass(cls):
        super(WizardTestMixin, cls).setUpClass()
        # This prevents auto-discovery, which would otherwise occur as soon as
        # tests start, creating unexpected starting conditions.
        wizard_pool._discovered = True
        cls.page_wizard = TestPageWizard(
            title=_(u"Page"),
            weight=100,
            form=PageWizardForm,
            model=Page,
        )
        # NOTE: This is rather nonsensical, but is quite useful for our tests.
        cls.user_settings_wizard = TestUserSettingsWizard(
            title=_(u"UserSettings"),
            weight=200,
            form=TitleWizardForm,
            model=UserSettings,
        )


class TestWizardPool(WizardTestMixin, CMSTestCase):

    def test_discover(self):
        """
        Tests that _discover() will register the page wizard.
        """
        wizard_pool._reset()
        self.assertFalse(wizard_pool._discovered)
        self.assertEqual(len(wizard_pool._entries), 0)
        wizard_pool._discover()
        self.assertTrue(len(wizard_pool._entries) > 0)
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
        wizards.sort(key=lambda e: getattr(e, 'weight'))
        entries = wizard_pool.get_entries()
        self.assertItemsEqual(entries, wizards)

        wizard_pool._clear()
        wizard_pool.register(self.user_settings_wizard)
        wizard_pool.register(self.page_wizard)
        wizards = [self.page_wizard, self.user_settings_wizard]
        wizards.sort(key=lambda e: getattr(e, 'weight'))
        entries = wizard_pool.get_entries()
        self.assertItemsEqual(entries, wizards)
