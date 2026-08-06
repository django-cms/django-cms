from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail

from cms.api import create_page_user
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
