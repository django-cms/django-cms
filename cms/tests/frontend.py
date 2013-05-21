# -*- coding: utf-8 -*-
from cms.api import create_page
from django.contrib.auth.models import User
from django.utils.unittest.case import SkipTest, skipIf

try:
    from selenium.webdriver.firefox.webdriver import WebDriver
    from selenium.common.exceptions import NoSuchElementException
    from django.test import LiveServerTestCase
except ImportError:
    from django.test import TestCase as LiveServerTestCase
    WebDriver = NoSuchElementException = False


class CMSLiveTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if WebDriver:
            cls.selenium = WebDriver()
        super(CMSLiveTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'selenium'):
            cls.selenium.quit()
        super(CMSLiveTests, cls).tearDownClass()


class ToolbarBasicTests(CMSLiveTests):
    @skipIf(not WebDriver, 'Selenium not found or Django too old')
    def test_toolbar_login(self):
        create_page('Home', 'simple.html', 'en', published=True).publish()
        user = User()
        user.username = 'admin'
        user.set_password('admin')
        user.is_superuser = user.is_staff = user.is_active = True
        user.save()
        url = '%s/?edit' % self.live_server_url
        self.selenium.get(url)
        self.assertRaises(NoSuchElementException, self.selenium.find_element_by_class_name, 'cms_toolbar-item_logout')
        username_input = self.selenium.find_element_by_id("id_cms-username")
        username_input.send_keys('admin')
        password_input = self.selenium.find_element_by_id("id_cms-password")
        password_input.send_keys('admin')
        password_input.submit()
        self.assertTrue(self.selenium.find_element_by_class_name('cms_toolbar-item-navigation'))
