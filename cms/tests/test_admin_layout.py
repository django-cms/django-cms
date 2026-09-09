from unittest import skipUnless

from django.conf import settings

from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse


@skipUnless(settings.AUTH_USER_MODEL == "emailuserapp.EmailUser", "Requires the email-user test project")
class EmailUserLayoutTests(CMSTestCase):
    def test_add_form_fieldset(self):
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_reverse("emailuserapp_emailuser_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="email"')
        # Custom fieldsets must not depend on Django's removed wide class.
        self.assertNotRegex(response.content.decode(), r'<fieldset[^>]*class="[^"]*\bwide\b')
