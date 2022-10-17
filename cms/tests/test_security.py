from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import QueryDict

from cms.api import add_plugin, create_page
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils.testcases import CMSTestCase


class SecurityTests(CMSTestCase):
    """
    Test security issues by trying some naive requests to add/alter/delete data.
    """

    def get_data(self):
        page = create_page("page", "nav_playground.html", "en")
        placeholder = page.get_placeholders('en').get(slot='body')
        superuser = self.get_superuser()
        staff = self.get_staff_user_with_no_permissions()
        return page, placeholder, superuser, staff

    def test_add(self):
        """
        Test adding a plugin to a *PAGE*.
        """
        page, placeholder, superuser, staff = self.get_data()
        post_data = {}
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # log the user out and post the plugin data to the cms add-plugin URL.
        self.client.logout()
        endpoint = self.get_add_plugin_uri(
            placeholder,
            'TextPlugin',
            settings.LANGUAGES[0][0],
        )
        response = self.client.post(endpoint, post_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = endpoint
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(endpoint, post_data)
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
        self.assertEqual(plugin.body, 'body')  # check the body is as expected.
        # log the user out, try to edit the plugin
        self.client.logout()
        endpoint = self.get_change_plugin_uri(plugin)
        response = self.client.post(endpoint, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = endpoint
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(endpoint, plugin_data)
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
        endpoint = self.get_delete_plugin_uri(plugin)
        response = self.client.post(endpoint, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = endpoint
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(endpoint, plugin_data)
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
        endpoint = self.get_add_plugin_uri(placeholder, 'TextPlugin', settings.LANGUAGES[0][0])
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # log the user out and try to add a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(endpoint, post_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = endpoint
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        self.assertEqual(CMSPlugin.objects.count(), 0)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(endpoint, post_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 0)

    def test_edit_ph(self):
        """
        Test editing a *NON PAGE* plugin
        """
        page, placeholder, superuser, staff = self.get_data()
        plugin = add_plugin(placeholder, 'TextPlugin', 'en', body='body')
        endpoint = self.get_change_plugin_uri(plugin)
        plugin_data = {
            'body': 'newbody',
            'language': 'en',
            'plugin_id': plugin.pk,
        }
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # log the user out and try to edit a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(endpoint, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = endpoint
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        plugin = self.reload(plugin)
        self.assertEqual(plugin.body, 'body')
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(endpoint, plugin_data)
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
        endpoint = self.get_delete_plugin_uri(plugin)
        # log the user out and try to remove a plugin using PlaceholderAdmin
        self.client.logout()
        response = self.client.post(endpoint, plugin_data)
        # since the user is not logged in, they should be prompted to log in.
        self.assertEqual(response.status_code, 302)
        querystring = QueryDict('', mutable=True)
        querystring['next'] = endpoint
        expected_url = '/{lang}/admin/login/?{next}'.format(
            lang=settings.LANGUAGES[0][0],
            next=querystring.urlencode(safe='/')
        )
        self.assertRedirects(response, expected_url)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        # now log a staff user without permissions in and do the same as above.
        self.client.login(username=getattr(staff, get_user_model().USERNAME_FIELD),
                          password=getattr(staff, get_user_model().USERNAME_FIELD))
        response = self.client.post(endpoint, plugin_data)
        # the user is logged in and the security check fails, so it should 403.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CMSPlugin.objects.count(), 1)
