# -*- coding: utf-8 -*-
from cms.test.testcases import CMSTestCase
from cms.utils.permissions import mail_page_user_change
from django.core import mail


class MailTestCase(CMSTestCase):
    def setUp(self):
        mail.outbox = [] # reset outbox
        
    def test_01_mail_page_user_change(self):
        user = self.create_page_user("username", grant_all=True)
        mail_page_user_change(user)
        self.assertEqual(len(mail.outbox), 1)
