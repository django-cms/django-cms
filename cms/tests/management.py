# -*- coding: utf-8 -*-
from __future__ import with_statement
from StringIO import StringIO
from django.core import management

from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.api import create_page, add_plugin
from cms.management.commands import cms
from cms.management.commands.subcommands.list import plugin_report
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
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            link_plugin = add_plugin(placeholder, "LinkPlugin", "en",
                name="A Link", url="https://www.django-cms.org")
            self.assertEqual(
                CMSPlugin.objects.filter(plugin_type=PLUGIN).count(),
                2)
            self.assertEqual(
                CMSPlugin.objects.filter(plugin_type="LinkPlugin").count(), 
                1)            

            # create a CMSPlugin with an unsaved instance
            instanceless_plugin = CMSPlugin(language="en", plugin_type="TextPlugin")
            instanceless_plugin.save()

            # create a bogus CMSPlugin to simulate one which used to exist but 
            # is no longer installed
            bogus_plugin = CMSPlugin(language="en", plugin_type="BogusPlugin")
            bogus_plugin.save()

            report = plugin_report()

            # there should be reports for three plugin types
            self.assertEqual(
                len(report), 
                3)
                
            # check the bogus plugin 
            bogus_plugins_report = report[0]
            self.assertEqual(
                bogus_plugins_report["model"], 
                None)            

            self.assertEqual(
                bogus_plugins_report["type"], 
                u'BogusPlugin')            
            
            self.assertEqual(
                bogus_plugins_report["instances"][0], 
                bogus_plugin)            

            # check the link plugin 
            link_plugins_report = report[1]
            self.assertEqual(
                link_plugins_report["model"], 
                link_plugin.__class__)            

            self.assertEqual(
                link_plugins_report["type"], 
                u'LinkPlugin')            
            
            self.assertEqual(
                link_plugins_report["instances"][0].get_plugin_instance()[0], 
                link_plugin)            

            # check the text plugins 
            text_plugins_report = report[2]
            self.assertEqual(
                text_plugins_report["model"], 
                TextPlugin.model)            

            self.assertEqual(
                text_plugins_report["type"], 
                u'TextPlugin')            
            
            self.assertEqual(
                len(text_plugins_report["instances"]), 
                3)
                
            self.assertEqual(
                text_plugins_report["instances"][2], 
                instanceless_plugin)
                            
            self.assertEqual(
                text_plugins_report["unsaved_instances"], 
                [instanceless_plugin])
        
                        
    def test_delete_orphaned_plugins(self):
        apps = ["cms", "menus", "sekizai", "cms.test_utils.project.sampleapp"]
        with SettingsOverride(INSTALLED_APPS=apps):
            placeholder = Placeholder.objects.create(slot="test")
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            add_plugin(placeholder, TextPlugin, "en", body="en body")
            link_plugin = add_plugin(placeholder, "LinkPlugin", "en",
                name="A Link", url="https://www.django-cms.org")

            instanceless_plugin = CMSPlugin(
                language="en", plugin_type="TextPlugin")
            instanceless_plugin.save()

            # create a bogus CMSPlugin to simulate one which used to exist but 
            # is no longer installed
            bogus_plugin = CMSPlugin(language="en", plugin_type="BogusPlugin")
            bogus_plugin.save()

            report = plugin_report()

            # there should be reports for three plugin types
            self.assertEqual(
                len(report), 
                3)
                
            # check the bogus plugin 
            bogus_plugins_report = report[0]
            self.assertEqual(
                len(bogus_plugins_report["instances"]), 
                1)            

            # check the link plugin 
            link_plugins_report = report[1]
            self.assertEqual(
                len(link_plugins_report["instances"]), 
                1)                      

            # check the text plugins 
            text_plugins_report = report[2]
            self.assertEqual(
                len(text_plugins_report["instances"]), 
                3)            

            self.assertEqual(
                len(text_plugins_report["unsaved_instances"]), 
                1)
                

            management.call_command('cms', 'delete_orphaned_plugins', stdout=StringIO())
            report = plugin_report()

            # there should be reports for two plugin types (one should have been deleted)
            self.assertEqual(
                len(report), 
                2)
                
            # check the link plugin 
            link_plugins_report = report[0]
            self.assertEqual(
                len(link_plugins_report["instances"]), 
                1)                      

            # check the text plugins 
            text_plugins_report = report[1]
            self.assertEqual(
                len(text_plugins_report["instances"]), 
                2)            

            self.assertEqual(
                len(text_plugins_report["unsaved_instances"]), 
                0)
                
            
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
