from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import SimpleTestCase

from cms.api import create_page_user
from cms.test_utils.email import get_locmem_email_settings
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

    @patch("cms.utils.mail.EmailMultiAlternatives.send", side_effect=OSError("mail unavailable"))
    def test_send_mail_suppresses_backend_errors_by_default(self, send):
        send_mail("Subject", "admin/cms/mail/page_user_change.txt", ["user@example.com"])

        send.assert_called_once_with()

    def test_send_mail_sends_text_and_html_message_on_success(self):
        send_mail(
            "Subject",
            "admin/cms/mail/page_user_change.txt",
            ["user@example.com"],
            context={"user": SimpleNamespace(username="test-user"), "password": "test-password"},
            html_template="admin/cms/mail/page_user_change.html",
        )

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("test-user", message.body)
        self.assertEqual(len(message.alternatives), 1)
        html_body, mimetype = message.alternatives[0]
        self.assertIn("test-user", html_body)
        self.assertEqual(mimetype, "text/html")

    @patch("cms.utils.mail.EmailMultiAlternatives.send", side_effect=OSError("mail unavailable"))
    def test_send_mail_can_propagate_backend_errors(self, send):
        with self.assertRaisesRegex(OSError, "mail unavailable"):
            send_mail(
                "Subject",
                "admin/cms/mail/page_user_change.txt",
                ["user@example.com"],
                fail_silently=False,
            )

        send.assert_called_once_with()

    @patch("cms.utils.mail.EmailMultiAlternatives.send", side_effect=ValueError("invalid message"))
    def test_send_mail_does_not_suppress_unexpected_errors(self, send):
        with self.assertRaisesRegex(ValueError, "invalid message"):
            send_mail("Subject", "admin/cms/mail/page_user_change.txt", ["user@example.com"])

        send.assert_called_once_with()


class LocmemEmailSettingsTests(SimpleTestCase):
    def test_locmem_settings_use_the_supported_django_api(self):
        backend = "django.core.mail.backends.locmem.EmailBackend"
        expected = (
            {"MAILERS": {"default": {"BACKEND": backend}}}
            if hasattr(mail, "mailers")
            else {"EMAIL_BACKEND": backend}
        )

        self.assertEqual(get_locmem_email_settings(), expected)
