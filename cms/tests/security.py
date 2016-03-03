from __future__ import with_statement
from cms.api import create_page, add_plugin
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PLUGIN_ADD, 
    URL_CMS_PLUGIN_EDIT, URL_CMS_PLUGIN_REMOVE)
from django.conf import settings
from django.core.urlresolvers import reverse


class SecurityTests(CMSTestCase):
    """
    Test security issues by trying some naive requests to add/alter/delete data.
    """
    def get_data(self):
        page = create_page("page", "nav_playground.html", "en")
        placeholder = page.placeholders.get(slot='body')
        superuser = self.get_superuser()
        staff = self.get_staff_user_with_no_permissions()
        return page, placeholder, superuser, staff
    
    def test_add(self):
        """
        Test adding a plugin to a *PAGE*.
        """
        page, placeholder, superuser, staff = self.get_data()
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # log the user out and post the plugin data to the cms add-plugin URL.
        self.client.logout()
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertTemplateUsed(response, 'admin/login.html')
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username='staff', password='staff')
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 0)
        
    def test_edit(self):
        """
        Test editing a *PAGE* plugin
        """
        page, placeholder, superuser, staff = self.get_data()
        # create the plugin using a superuser
        plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
        plugin_data = {
            'plugin_id': plugin.pk,
            'body': 'newbody',
        }
        self.assertEqual(plugin.body, 'body') # check the body is as expected.
        # log the user out, try to edit the plugin
        self.client.logout()
        url = URL_CMS_PLUGIN_EDIT + '%s/' % plugin.pk
        response = self.client.post(url, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertTemplateUsed(response, 'admin/login.html')
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username='staff', password='staff')
        response = self.client.post(url, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
    
    def test_delete(self):
        """
        Test deleting a *PAGE* plugin
        """
        page, placeholder, superuser, staff = self.get_data()
        plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
        plugin_data = {
            'plugin_id': plugin.pk,
        }
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # log the user out, try to remove the plugin
        self.client.logout()
        response = self.client.post(URL_CMS_PLUGIN_REMOVE, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertTemplateUsed(response, 'admin/login.html')
        self.assertEqual(CMSPlugin.objects.count(), 1)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username='staff', password='staff')
        response = self.client.post(URL_CMS_PLUGIN_REMOVE, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        
    def test_add_ph(self):
        """
        Test adding a *NON PAGE* plugin
        """
        page, placeholder, superuser, staff = self.get_data()
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        url = reverse('admin:placeholderapp_example1_add_plugin')
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # log the user out and try to add a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(url, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertTemplateUsed(response, 'admin/login.html')
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username='staff', password='staff')
        response = self.client.post(url, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 0)
    
    def test_edit_ph(self):
        """
        Test editing a *NON PAGE* plugin
        """
        page, placeholder, superuser, staff = self.get_data()
        plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
        url = reverse('admin:placeholderapp_example1_edit_plugin', args=(plugin.pk,))
        plugin_data = {
            'body': 'newbody',
            'language': 'en',
            'plugin_id': plugin.pk,
        }
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # log the user out and try to edit a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(url, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertTemplateUsed(response, 'admin/login.html')
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username='staff', password='staff')
        response = self.client.post(url, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
    
    def test_delete_ph(self):
        page, placeholder, superuser, staff = self.get_data()
        plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
        plugin_data = {
            'plugin_id': plugin.pk,
        }
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        url = reverse('admin:placeholderapp_example1_remove_plugin')
        # log the user out and try to remove a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(url, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertTemplateUsed(response, 'admin/login.html')
        self.assertEqual(CMSPlugin.objects.count(), 1)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username='staff', password='staff')
        response = self.client.post(url, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        
    def test_text_plugin_xss(self):
        page, placeholder, superuser, staff = self.get_data()
        with self.login_user_context(superuser):
            plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
            # ACTUAL TEST STARTS HERE.
            data = {
                "body": "<div onload='do_evil_stuff();'>divcontent</div><a href='javascript:do_evil_stuff()'>acontent</a>"
            }
            edit_url = '%s%s/' % (URL_CMS_PLUGIN_EDIT, plugin.pk)
            response = self.client.post(edit_url, data)
            self.assertEquals(response.status_code, 200)
            txt = Text.objects.all()[0]
            self.assertEquals(txt.body, '<div>divcontent</div><a>acontent</a>')
