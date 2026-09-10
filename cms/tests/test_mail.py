from smtplib import SMTPException
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.test import SimpleTestCase, override_settings

from cms.api import create_page_user
from cms.test_utils.mail import MAILERS_SUPPORTED
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mail import mail_page_user_change, send_mail


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


@override_settings(
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {
                            "mail.txt": "{{ title }}: {{ login_url }}",
                            "mail.html": "<p>{{ title }}</p>",
                        },
                    )
                ]
            },
        }
    ]
)
class MailDeliveryTests(SimpleTestCase):
    def send_message(self, **kwargs):
        return send_mail(
            "Account updated",
            "mail.txt",
            ["user@example.com"],
            site=Site(domain="example.com"),
            **kwargs,
        )

    def test_text_mail(self):
        self.send_message()
        message = mail.outbox[0]
        self.assertEqual(message.to, ["user@example.com"])
        self.assertIn("Account updated: https://example.com/", message.body)
        self.assertEqual(message.alternatives, [])

    def test_multipart_mail(self):
        self.send_message(html_template="mail.html")
        self.assertEqual(mail.outbox[0].alternatives, [("<p>Account updated</p>", "text/html")])

    def test_suppress_delivery_errors(self):
        for error in (ConnectionError, SMTPException):
            with self.subTest(error=error), patch("cms.utils.mail.EmailMultiAlternatives.send", side_effect=error):
                self.send_message()

    def test_raise_delivery_errors(self):
        for error in (ConnectionError, SMTPException):
            with self.subTest(error=error), patch("cms.utils.mail.EmailMultiAlternatives.send", side_effect=error):
                with self.assertRaises(error):
                    self.send_message(fail_silently=False)

    def test_raise_programming_errors(self):
        with patch("cms.utils.mail.EmailMultiAlternatives.send", side_effect=ValueError):
            with self.assertRaises(ValueError):
                self.send_message()

    @skipUnless(MAILERS_SUPPORTED, "Django < 6.1 has no MAILERS setting")
    @override_settings(MAILERS={})
    def test_unconfigured_mailer(self):
        self.send_message()
        with self.assertRaises(mail.MailerDoesNotExist):
            self.send_message(fail_silently=False)
