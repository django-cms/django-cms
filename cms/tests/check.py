# -*- coding: utf-8 -*-
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
    def assertCheck(self, successful, errors, successes, skips, warnings):
        output = TestOutput()
        check(output)
        self.assertEqual(output.successful, successful)
        self.assertEqual(output.errors, errors)
        self.assertEqual(output.successes, successes)
        self.assertEqual(output.skips, skips)
        self.assertEqual(output.warnings, warnings)

    def test_test_confs(self):
        self.assertCheck(True, 0, 7, 1, 0)

    def test_cms_moderator_deprecated(self):
        with SettingsOverride(CMS_MODERATOR=True):
            self.assertCheck(True, 0, 7, 0, 1)

    def test_cms_flat_urls_deprecated(self):
        with SettingsOverride(CMS_FLAT_URLS=True):
            self.assertCheck(True, 0, 7, 0, 1)

    def test_no_sekizai(self):
        with SettingsOverride(INSTALLED_APPS=[]):
            self.assertCheck(False, 2, 5, 1, 0)

    def test_no_sekizai_template_context_processor(self):
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[]):
            self.assertCheck(False, 2, 5, 1, 0)

    def test_old_style_i18n_settings(self):
        with SettingsOverride(CMS_LANGUAGES=[('en', 'English')]):
            self.assertCheck(True, 0, 6, 1, 1)

    def test_cms_hide_untranslated_deprecated(self):
        with SettingsOverride(CMS_HIDE_UNTRANSLATED=True):
            self.assertCheck(True, 0, 7, 1, 1)

    def test_cms_language_fallback_deprecated(self):
        with SettingsOverride(CMS_LANGUAGE_FALLBACK=True):
            self.assertCheck(True, 0, 7, 1, 1)

    def test_cms_language_conf_deprecated(self):
        with SettingsOverride(CMS_LANGUAGE_CONF=True):
            self.assertCheck(True, 0, 7, 1, 1)

    def test_cms_site_languages_deprecated(self):
        with SettingsOverride(CMS_SITE_LANGUAGES=True):
            self.assertCheck(True, 0, 7, 1, 1)

    def test_cms_frontend_languages_deprecated(self):
        with SettingsOverride(CMS_FRONTEND_LANGUAGES=True):
            self.assertCheck(True, 0, 7, 1, 1)
