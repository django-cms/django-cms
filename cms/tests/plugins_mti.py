# -*- coding: utf-8 -*-

from django.conf import settings

from cms.models import Page
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.testcases import (
    URL_CMS_PAGE_ADD,
    URL_CMS_PLUGIN_ADD,
    URL_CMS_PLUGIN_EDIT,
)

from cms.test_utils.project.mti_pluginapp.models import TestPluginBetaModel

from .plugins import PluginsTestBaseCase


# class CustomPluginsTestCase(PluginsTestBaseCase):

#     def test_add_edit_plugin(self):
#         """
#         Test that we can instantiate and use a MTI plugin
#         """

#         INSTALLED_APPS = settings.INSTALLED_APPS
#         INSTALLED_APPS = INSTALLED_APPS + ['cms.test_utils.project.mti_pluginapp']

#         with SettingsOverride(INSTALLED_APPS):

#             # Create a page
#             page_data = self.get_new_page_data()
#             self.client.post(URL_CMS_PAGE_ADD, page_data)
#             page = Page.objects.all()[0]

#             # Add the MTI plugin
#             plugin_data = {
#                 'plugin_type': "TestPluginBeta",
#                 'plugin_language': settings.LANGUAGES[0][0],
#                 'placeholder_id': page.placeholders.get(slot="body").pk,
#                 'plugin_parent': '',
#             }
#             response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
#             self.assertEqual(response.status_code, 200)
#             plugin_id = self.get_response_pk(response)
#             self.assertEqual(plugin_id, CMSPlugin.objects.all()[0].pk)

#             # Test we can open the change form for the MTI plugin
#             edit_url = "%s%s/" % (URL_CMS_PLUGIN_EDIT, plugin_id)
#             response = self.client.get(edit_url)
#             self.assertEqual(response.status_code, 200)

#             # Edit the MTI plugin
#             data = {
#                 "alpha": "ALPHA",
#                 "beta": "BETA"
#             }
#             response = self.client.post(edit_url, data)
#             self.assertEqual(response.status_code, 200)

#             # Test that the change was properly stored in the DB
#             plugin_model = TestPluginBetaModel.objects.all()[0]
#             self.assertEqual("BETA", plugin_model.body)
