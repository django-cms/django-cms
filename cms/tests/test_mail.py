from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail

from cms.api import create_page_user
from cms.test_utils.mail import MAILERS_SUPPORTED
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mail import mail_page_user_change


class MailTestCase(CMSTestCase):
    def setUp(self):
        mail.outbox = []  # reset outbox

    def test_mail_page_user_change(self):
        user = get_user_model().objects.create_superuser("username", "username@django-cms.org", "username")
        user = create_page_user(user, user, grant_all=True)
        mail_page_user_change(user)
        self.assertEqual(len(mail.outbox), 1)

    @skipUnless(MAILERS_SUPPORTED, "Django < 6.1 has no MAILERS setting")
    def test_mailers_only_project(self):
        self.assertEqual(
            settings.MAILERS["default"]["BACKEND"],
            "django.core.mail.backends.locmem.EmailBackend",
        )
        # MAILERS must work without falling back to legacy email settings.
        for name in ("EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_HOST_USER"):
            with self.subTest(setting=name), self.assertRaises(AttributeError):
                getattr(settings, name)

        user = get_user_model()(email="username@django-cms.org")
        mail_page_user_change(user, site=Site(domain="example.com"))

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [user.email])
        self.assertIn("https://example.com/en/admin/", message.body)
        self.assertEqual(message.alternatives[0][1], "text/html")
