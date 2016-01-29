# -*- coding: utf-8 -*-
from __future__ import with_statement
from copy import deepcopy
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateSyntaxError, base
from django.test import TestCase

from cms.api import add_plugin
from cms.models.pluginmodel import CMSPlugin
from cms.models.placeholdermodel import Placeholder
from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import ArticlePluginModel
from cms.test_utils.project.extensionapp.models import MyPageExtension
from cms.utils.check import FileOutputWrapper, check, FileSectionWrapper
from cms.utils.compat import DJANGO_1_6, DJANGO_1_7, DJANGO_1_8
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

    def test_cms_moderator_deprecated(self):
        with self.settings(CMS_MODERATOR=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_flat_urls_deprecated(self):
        with self.settings(CMS_FLAT_URLS=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_no_sekizai(self):
        if DJANGO_1_6:
            with self.settings(INSTALLED_APPS=['cms', 'menus']):
                old_libraries = base.libraries
                base.libraries = {}
                old_templatetags_modules = base.templatetags_modules
                base.templatetags_modules = []
                self.assertRaises(TemplateSyntaxError, check, TestOutput())
                base.libraries = old_libraries
                base.templatetags_modules = old_templatetags_modules
        elif DJANGO_1_7:
            from django.apps import apps
            apps.set_available_apps(['cms', 'menus'])
            old_libraries = base.libraries
            base.libraries = {}
            old_templatetags_modules = base.templatetags_modules
            base.templatetags_modules = []
            self.assertRaises(TemplateSyntaxError, check, TestOutput())
            base.libraries = old_libraries
            base.templatetags_modules = old_templatetags_modules
            apps.unset_available_apps()
        elif DJANGO_1_8:
            from django.apps import apps
            base.get_templatetags_modules.cache_clear()
            apps.set_available_apps(['cms', 'menus'])
            self.assertCheck(False, errors=2)
            apps.unset_available_apps()
        else:
            from django.apps import apps
            apps.set_available_apps(['cms', 'menus'])
            self.assertCheck(False, errors=2)
            apps.unset_available_apps()

    def test_no_sekizai_template_context_processor(self):
        if DJANGO_1_7:
            override = {'TEMPLATE_CONTEXT_PROCESSORS': []}
        else:
            override = {'TEMPLATES': deepcopy(settings.TEMPLATES)}
            override['TEMPLATES'][0]['OPTIONS']['context_processors'] = []
        with self.settings(**override):
            self.assertCheck(False, errors=2)

    def test_old_style_i18n_settings(self):
        with self.settings(CMS_LANGUAGES=[('en', 'English')]):
            self.assertRaises(ImproperlyConfigured, self.assertCheck, True, warnings=1, errors=0)

    def test_cms_hide_untranslated_deprecated(self):
        with self.settings(CMS_HIDE_UNTRANSLATED=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_language_fallback_deprecated(self):
        with self.settings(CMS_LANGUAGE_FALLBACK=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_language_conf_deprecated(self):
        with self.settings(CMS_LANGUAGE_CONF=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_middlewares(self):
        MIDDLEWARE_CLASSES=[
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
        with self.settings(MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES):
            self.assertCheck(False, warnings=0, errors=2)

    def test_cms_site_languages_deprecated(self):
        with self.settings(CMS_SITE_LANGUAGES=True):
            self.assertCheck(True, warnings=1, errors=0)

    def test_cms_frontend_languages_deprecated(self):
        with self.settings(CMS_FRONTEND_LANGUAGES=True):
            self.assertCheck(True, warnings=1, errors=0)

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

    def test_placeholder_tag_deprecation(self):
        self.assertCheck(True, warnings=0, errors=0)
        alt_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'test_utils',
            'project',
            'alt_templates'
        )
        if DJANGO_1_7:
            with self.settings(TEMPLATE_DIRS=[alt_dir], CMS_TEMPLATES=[]):
                self.assertCheck(True, warnings=1, errors=0)
        else:
            NEWTEMPLATES = deepcopy(settings.TEMPLATES)
            NEWTEMPLATES[0]['DIRS'] = [alt_dir]
            with self.settings(TEMPLATES=NEWTEMPLATES, CMS_TEMPLATES=[]):
                self.assertCheck(True, warnings=1, errors=0)

    def test_non_numeric_site_id(self):
        self.assertCheck(True, warnings=0, errors=0)
        with self.settings(SITE_ID='broken'):
            self.assertCheck(False, warnings=0, errors=1)


class CheckWithDatabaseTests(CheckAssertMixin, TestCase):

    def test_check_plugin_instances(self):
        self.assertCheck(True, warnings=0, errors=0 )

        apps = ["cms", "menus", "sekizai", "cms.test_utils.project.sampleapp", "treebeard"]
        with self.settings(INSTALLED_APPS=apps):
            placeholder = Placeholder.objects.create(slot="test")
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            add_plugin(placeholder, "LinkPlugin", "en",
                       name="A Link", url="https://www.django-cms.org")

            # create a CMSPlugin with an unsaved instance
            instanceless_plugin = CMSPlugin(language="en", plugin_type="TextPlugin")
            instanceless_plugin.save()

            self.assertCheck(False, warnings=0, errors=2)

            # create a bogus CMSPlugin to simulate one which used to exist but
            # is no longer installed
            bogus_plugin = CMSPlugin(language="en", plugin_type="BogusPlugin")
            bogus_plugin.save()

            self.assertCheck(False, warnings=0, errors=3)
