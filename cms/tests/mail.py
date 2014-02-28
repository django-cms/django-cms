# -*- coding: utf-8 -*-
from cms.api import create_page_user
from cms.compat import get_user_model
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mail import mail_page_user_change
from django.core import mail


class MailTestCase(CMSTestCase):
    def setUp(self):
        mail.outbox = [] # reset outbox
        
    def test_mail_page_user_change(self):
        user = get_user_model().objects.create_superuser("username", "username@django-cms.org", "username")
        user = create_page_user(user, user, grant_all=True)
        mail_page_user_change(user)
        self.assertEqual(len(mail.outbox), 1)
