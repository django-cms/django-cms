# -*- coding: utf-8 -*-
from copy import deepcopy

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from cms.api import add_plugin
from cms.models.pluginmodel import CMSPlugin
from cms.models.placeholdermodel import Placeholder
from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import ArticlePluginModel
from cms.test_utils.project.extensionapp.models import MyPageExtension
from cms.utils.check import FileOutputWrapper, check, FileSectionWrapper

from djangocms_text_ckeditor.cms_plugins import TextPlugin


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


class CheckAssertMixin(object):
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


class CheckTests(CheckAssertMixin, TestCase):
    def test_test_confs(self):
        self.assertCheck(True, errors=0, warnings=0)

    def test_no_sekizai(self):
        apps = list(settings.INSTALLED_APPS)
        apps.remove('sekizai')

        with self.settings(INSTALLED_APPS=apps):
            self.assertCheck(False, errors=1)

    def test_no_cms_settings_context_processor(self):
        override = {'TEMPLATES': deepcopy(settings.TEMPLATES)}
        override['TEMPLATES'][0]['OPTIONS']['context_processors'] = ['sekizai.context_processors.sekizai']
        with self.settings(**override):
            self.assertCheck(False, errors=1)

    def test_no_sekizai_template_context_processor(self):
        override = {'TEMPLATES': deepcopy(settings.TEMPLATES)}
        override['TEMPLATES'][0]['OPTIONS']['context_processors'] = ['cms.context_processors.cms_settings']
        with self.settings(**override):
            self.assertCheck(False, errors=2)

    def test_old_style_i18n_settings(self):
        with self.settings(CMS_LANGUAGES=[('en', 'English')]):
            self.assertRaises(ImproperlyConfigured, self.assertCheck, True, warnings=1, errors=0)

    def test_middlewares(self):
        MIDDLEWARE = [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.http.ConditionalGetMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
        ]
        self.assertCheck(True, warnings=0, errors=0)
        with self.settings(MIDDLEWARE=MIDDLEWARE):
            self.assertCheck(False, warnings=0, errors=2)

    def test_copy_relations_fk_check(self):
        """
        this is ugly, feel free to come up with a better test
        """
        self.assertCheck(True, warnings=0, errors=0)
        copy_rel = ArticlePluginModel.copy_relations
        del ArticlePluginModel.copy_relations
        self.assertCheck(True, warnings=2, errors=0)
        ArticlePluginModel.copy_relations = copy_rel

    def test_copy_relations_on_page_extension(self):
        """
        Agreed. It is ugly, but it works.
        """
        self.assertCheck(True, warnings=0, errors=0)
        copy_rel = MyPageExtension.copy_relations
        del MyPageExtension.copy_relations
        self.assertCheck(True, warnings=1, errors=0)
        MyPageExtension.copy_relations = copy_rel

    def test_non_numeric_site_id(self):
        self.assertCheck(True, warnings=0, errors=0)
        with self.settings(SITE_ID='broken'):
            self.assertCheck(False, warnings=0, errors=1)


class CheckWithDatabaseTests(CheckAssertMixin, TestCase):

    def test_check_plugin_instances(self):
        self.assertCheck(True, warnings=0, errors=0 )

        placeholder = Placeholder.objects.create(slot="test")
        add_plugin(placeholder, TextPlugin, "en", body="en body")
        add_plugin(placeholder, TextPlugin, "en", body="en body")
        add_plugin(placeholder, "LinkPlugin", "en",
                   name="A Link", external_link="https://www.django-cms.org")

        # create a CMSPlugin with an unsaved instance
        instanceless_plugin = CMSPlugin(language="en", plugin_type="TextPlugin")
        instanceless_plugin.save()

        self.assertCheck(False, warnings=0, errors=2)

        # create a bogus CMSPlugin to simulate one which used to exist but
        # is no longer installed
        bogus_plugin = CMSPlugin(language="en", plugin_type="BogusPlugin")
        bogus_plugin.save()

        self.assertCheck(False, warnings=0, errors=3)
