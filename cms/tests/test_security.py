from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.utils.http import urlencode
from djangocms_text_ckeditor.models import Text

from cms.api import create_page, add_plugin
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PLUGIN_ADD,
                                      URL_CMS_PLUGIN_EDIT,
                                      URL_CMS_PLUGIN_REMOVE)
from cms.utils.urlutils import admin_reverse


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
        get_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
        }
        post_data = {}
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # log the user out and post the plugin data to the cms add-plugin URL.
        self.client.logout()
        add_url = URL_CMS_PLUGIN_ADD + '?' + urlencode(get_data)
        response = self.client.post(add_url, post_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = add_url
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(add_url, post_data)
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
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/admin/login/?next=%s' % url)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
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
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/admin/login/?next=%s' % URL_CMS_PLUGIN_REMOVE)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(URL_CMS_PLUGIN_REMOVE + "%s/" % plugin.pk, plugin_data)
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
        post_data = {}
        get_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
        }
        add_url = (
            admin_reverse('placeholderapp_example1_add_plugin') + '?' +
            urlencode(get_data)
        )
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # log the user out and try to add a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(add_url, post_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = add_url
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(add_url, post_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 0)

    def test_edit_ph(self):
        """
        Test editing a *NON PAGE* plugin
        """
        page, placeholder, superuser, staff = self.get_data()
        plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
        url = admin_reverse('placeholderapp_example1_edit_plugin', args=(plugin.pk,))
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
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/admin/login/?next=%s' % url)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
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
        url = admin_reverse('placeholderapp_example1_delete_plugin', args=[plugin.pk])
        # log the user out and try to remove a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(url, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/admin/login/?next=%s' % url)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
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
            self.assertEqual(response.status_code, 200)
            txt = Text.objects.all()[0]
            self.assertEqual(txt.body, '<div>divcontent</div><a>acontent</a>')
