# -*- coding: utf-8 -*-
from __future__ import with_statement
from StringIO import StringIO
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.api import create_page, add_plugin
from cms.management.commands import cms
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title
from cms.models.placeholdermodel import Placeholder
from cms.plugins.text.cms_plugins import TextPlugin

APPHOOK = "SampleApp"
PLUGIN = "TextPlugin"

class ManagementTestCase(CMSTestCase):

    def test_list_apphooks(self):
        out = StringIO()
        apps = ["cms", "menus", "sekizai", "cms.test_utils.project.sampleapp"]
        with SettingsOverride(INSTALLED_APPS=apps):
            create_page('Hello Title', "nav_playground.html", "en", apphook=APPHOOK)
            self.assertEqual(Title.objects.filter(application_urls=APPHOOK).count(), 1)            
            command = cms.Command()
            command.stdout = out
            command.handle("list", "apphooks", interactive=False)
            self.assertEqual(out.getvalue(), "SampleApp\n")
            
    def test_uninstall_apphooks_without_apphook(self):
        out = StringIO()
        command = cms.Command()
        command.stdout = out
        command.handle("uninstall", "apphooks", APPHOOK, interactive=False)
        self.assertEqual(out.getvalue(), "no 'SampleApp' apphooks found\n")

    def test_uninstall_apphooks_with_apphook(self):
        out = StringIO()
        apps = ["cms", "menus", "sekizai", "cms.test_utils.project.sampleapp"]
        with SettingsOverride(INSTALLED_APPS=apps):
            create_page('Hello Title', "nav_playground.html", "en", apphook=APPHOOK)
            self.assertEqual(Title.objects.filter(application_urls=APPHOOK).count(), 1)
            command = cms.Command()
            command.stdout = out
            command.handle("uninstall", "apphooks", APPHOOK, interactive=False)
            self.assertEqual(out.getvalue(), "1 'SampleApp' apphooks uninstalled\n")
            self.assertEqual(Title.objects.filter(application_urls=APPHOOK).count(), 0)

    def test_list_plugins(self):
        out = StringIO()
        apps = ["cms", "menus", "sekizai", "cms.test_utils.project.sampleapp"]
        with SettingsOverride(INSTALLED_APPS=apps):
            placeholder = Placeholder.objects.create(slot="test")
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            self.assertEqual(CMSPlugin.objects.filter(plugin_type=PLUGIN).count(), 1)            
            command = cms.Command()
            command.stdout = out
            command.handle("list", "plugins", interactive=False)
            self.assertEqual(out.getvalue(), "TextPlugin\n")
            
    def test_uninstall_plugins_without_plugin(self):
        out = StringIO()
        command = cms.Command()
        command.stdout = out
        command.handle("uninstall", "plugins", PLUGIN, interactive=False)
        self.assertEqual(out.getvalue(), "no 'TextPlugin' plugins found\n")

    def test_uninstall_plugins_with_plugin(self):
        out = StringIO()
        apps = ["cms", "menus", "sekizai", "cms.test_utils.project.sampleapp"]
        with SettingsOverride(INSTALLED_APPS=apps):
            placeholder = Placeholder.objects.create(slot="test")
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            self.assertEqual(CMSPlugin.objects.filter(plugin_type=PLUGIN).count(), 1)
            command = cms.Command()
            command.stdout = out
            command.handle("uninstall", "plugins", PLUGIN, interactive=False)
            self.assertEqual(out.getvalue(), "1 'TextPlugin' plugins uninstalled\n")
            self.assertEqual(CMSPlugin.objects.filter(plugin_type=PLUGIN).count(), 0)
