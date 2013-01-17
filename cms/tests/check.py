# -*- coding: utf-8 -*-
from __future__ import with_statement
from unittest import TestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.check import FileOutputWrapper, check, FileSectionWrapper


class TestOutput(FileOutputWrapper):
    def __init__(self):
        super(TestOutput, self).__init__(None, None)
        self.section_wrapper = TestSectionOutput

    def write(self, message):
        pass

    def write_stderr(self, message):
        pass


class TestSectionOutput(FileSectionWrapper):
    def write(self, message):
        pass

    def write_stderr(self, message):
        pass


class CheckTests(TestCase):
    def assertCheck(self, successful, **assertions):
        """
        asserts that checks are successful or not
        Assertions is a mapping of numbers to check (eg successes=5)
        """
        output = TestOutput()
        check(output)
        self.assertEqual(output.successful, successful)
        for key, value in assertions.items():
            self.assertEqual(getattr(output, key), value, "%s %s expected, got %s" % (value, key, getattr(output, key)))

    def test_test_confs(self):
        self.assertCheck(True, errors=0, warnings=0)

    def test_cms_moderator_deprecated(self):
        with SettingsOverride(CMS_MODERATOR=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_flat_urls_deprecated(self):
        with SettingsOverride(CMS_FLAT_URLS=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_no_sekizai(self):
        with SettingsOverride(INSTALLED_APPS=[]):
            self.assertCheck(False, errors=2)

    def test_no_sekizai_template_context_processor(self):
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[]):
            self.assertCheck(False, errors=2)

    def test_old_style_i18n_settings(self):
        with SettingsOverride(CMS_LANGUAGES=[('en', 'English')]):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_hide_untranslated_deprecated(self):
        with SettingsOverride(CMS_HIDE_UNTRANSLATED=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_language_fallback_deprecated(self):
        with SettingsOverride(CMS_LANGUAGE_FALLBACK=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_language_conf_deprecated(self):
        with SettingsOverride(CMS_LANGUAGE_CONF=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_site_languages_deprecated(self):
        with SettingsOverride(CMS_SITE_LANGUAGES=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_frontend_languages_deprecated(self):
        with SettingsOverride(CMS_FRONTEND_LANGUAGES=True):
            self.assertCheck(True, warnings=1, errors=0 )
