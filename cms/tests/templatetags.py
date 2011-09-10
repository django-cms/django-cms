from __future__ import with_statement
from cms.models.pagemodel import Page
from cms.templatetags.cms_tags import get_site_id, _get_page_by_untyped_arg
from cms.test_utils.fixtures.templatetags import TwoPagesFixture
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.plugins import get_placeholders
from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from unittest import TestCase


class TemplatetagTests(TestCase):
    def test_get_site_id_from_nothing(self):
        with SettingsOverride(SITE_ID=10):
            self.assertEqual(10, get_site_id(None))
        
    def test_get_site_id_from_int(self):
        self.assertEqual(10, get_site_id(10))
        
    def test_get_site_id_from_site(self):
        site = Site()
        site.id = 10
        self.assertEqual(10, get_site_id(site))
        
    def test_get_site_id_from_str_int(self):
        self.assertEqual(10, get_site_id('10'))
        
    def test_get_site_id_from_str(self):
        with SettingsOverride(SITE_ID=10):
            self.assertEqual(10, get_site_id("something"))
    
    def test_unicode_placeholder_name_fails_fast(self):
        self.assertRaises(ImproperlyConfigured, get_placeholders, 'unicode_placeholder.html')


class TemplatetagDatabaseTests(TwoPagesFixture, SettingsOverrideTestCase):
    settings_overrides = {'CMS_MODERATOR': False}
    
    def _getfirst(self):
        return Page.objects.get(title_set__title='first')
    
    def _getsecond(self):
        return Page.objects.get(title_set__title='second')
    
    def test_get_page_by_untyped_arg_none(self):
        control = self._getfirst()
        request = self.get_request('/')
        request.current_page = control
        page = _get_page_by_untyped_arg(None, request, 1)
        self.assertEqual(page, control)
        
    def test_get_page_by_untyped_arg_page(self):
        control = self._getfirst()
        request = self.get_request('/')
        page = _get_page_by_untyped_arg(control, request, 1)
        self.assertEqual(page, control)
        
    def test_get_page_by_untyped_arg_reverse_id(self):
        second = self._getsecond()
        request = self.get_request('/')
        page = _get_page_by_untyped_arg("myreverseid", request, 1)
        self.assertEqual(page, second)
        
    def test_get_page_by_untyped_arg_dict(self):
        second = self._getsecond()
        request = self.get_request('/')
        page = _get_page_by_untyped_arg({'pk': second.pk}, request, 1)
        self.assertEqual(page, second)
        
    def test_get_page_by_untyped_arg_dict_fail_debug(self):
        with SettingsOverride(DEBUG=True):
            request = self.get_request('/')
            self.assertRaises(Page.DoesNotExist,
                _get_page_by_untyped_arg, {'pk': 3}, request, 1
            )
            self.assertEqual(len(mail.outbox), 0)
            
    def test_get_page_by_untyped_arg_dict_fail_nodebug_do_email(self):
        with SettingsOverride(SEND_BROKEN_LINK_EMAILS=True, DEBUG=False, MANAGERS=[("Jenkins", "tests@django-cms.org")]):
            request = self.get_request('/')
            page = _get_page_by_untyped_arg({'pk': 3}, request, 1)
            self.assertEqual(page, None)
            self.assertEqual(len(mail.outbox), 1)

    def test_get_page_by_untyped_arg_dict_fail_nodebug_no_email(self):
        with SettingsOverride(SEND_BROKEN_LINK_EMAILS=False, DEBUG=False, MANAGERS=[("Jenkins", "tests@django-cms.org")]):
            request = self.get_request('/')
            page = _get_page_by_untyped_arg({'pk': 3}, request, 1)
            self.assertEqual(page, None)
            self.assertEqual(len(mail.outbox), 0)
    
    def test_get_page_by_untyped_arg_fail(self):
        request = self.get_request('/')
        self.assertRaises(TypeError, _get_page_by_untyped_arg, [], request, 1)