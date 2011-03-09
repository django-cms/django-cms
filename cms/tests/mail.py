# -*- coding: utf-8 -*-
from cms.api import create_page_user
from cms.test_utils.testcases import CMSTestCase
from cms.utils.permissions import mail_page_user_change
from django.contrib.auth.models import User
from django.core import mail


class MailTestCase(CMSTestCase):
    def setUp(self):
        mail.outbox = [] # reset outbox
        
    def test_01_mail_page_user_change(self):
        user = User.objects.create_superuser("username", "username@django-cms.org", "username")
        user = create_page_user(user, user, grant_all=True)
        mail_page_user_change(user)
        self.assertEqual(len(mail.outbox), 1)
