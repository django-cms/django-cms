# -*- coding: utf-8 -*-
from cms.api import create_page
from cms.models import Page
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.testcases import CMSTestCase
from django.contrib.sites.models import Site
from django.db import connections
from django.utils import unittest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
from django.test import LiveServerTestCase, TestCase
import os

from cms.compat import get_user_model


class CMSLiveTests(LiveServerTestCase, CMSTestCase):
    @classmethod
    def setUpClass(cls):
        super(CMSLiveTests, cls).setUpClass()
        if os.environ.get('SELENIUM', '') != '':
            #skip selenium tests
            raise unittest.SkipTest("Selenium env is set to 0")
        if os.environ.get("TRAVIS_BUILD_NUMBER"):
            capabilities = webdriver.DesiredCapabilities.CHROME
            capabilities['version'] = '31'
            capabilities['platform'] = 'OS X 10.9'
            capabilities['name'] = 'django CMS'
            capabilities['build'] = os.environ.get("TRAVIS_BUILD_NUMBER")
            capabilities['tags'] = [os.environ.get("TRAVIS_PYTHON_VERSION"), "CI"]
            username = os.environ.get("SAUCE_USERNAME")
            access_key = os.environ.get("SAUCE_ACCESS_KEY")
            capabilities["tunnel-identifier"] = os.environ.get("TRAVIS_JOB_NUMBER")
            hub_url = "http://%s:%s@ondemand.saucelabs.com/wd/hub" % (username, access_key)
            cls.driver = webdriver.Remote(desired_capabilities=capabilities, command_executor=hub_url)
            cls.driver.implicitly_wait(30)
        else:
            cls.driver = webdriver.Firefox()
            cls.driver.implicitly_wait(5)
        cls.accept_next_alert = True

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super(CMSLiveTests, cls).tearDownClass()

    def tearDown(self):
        super(CMSLiveTests, self).tearDown()
        Page.objects.all().delete() # somehow the sqlite transaction got lost.


    def wait_until(self, callback, timeout=10):
        """
        Helper function that blocks the execution of the tests until the
        specified callback returns a value that is not falsy. This function can
        be called, for example, after clicking a link or submitting a form.
        See the other public methods that call this function for more details.
        """
        from selenium.webdriver.support.wait import WebDriverWait

        WebDriverWait(self.driver, timeout).until(callback)

    def wait_loaded_tag(self, tag_name, timeout=10):
        """
        Helper function that blocks until the element with the given tag name
        is found on the page.
        """
        self.wait_until(
            lambda driver: driver.find_element_by_tag_name(tag_name),
            timeout
        )

    def wait_page_loaded(self):
        """
        Block until page has started to load.
        """
        from selenium.common.exceptions import TimeoutException

        try:
            # Wait for the next page to be loaded
            self.wait_loaded_tag('body')
        except TimeoutException:
            # IE7 occasionnally returns an error "Internet Explorer cannot
            # display the webpage" and doesn't load the next page. We just
            # ignore it.
            pass

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException:
            return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True


class ToolbarBasicTests(CMSLiveTests):

    def setUp(self):
        self.user = self._create_user('admin', True, True, True)
        Site.objects.create(domain='example.org', name='example.org')
        self.base_url = self.live_server_url
        self.driver.implicitly_wait(2)
        super(ToolbarBasicTests, self).setUp()

    def test_toolbar_login(self):
        User = get_user_model()
        create_page('Home', 'simple.html', 'en', published=True)
        url = '%s/?edit' % self.live_server_url
        self.assertTrue(User.objects.all().count(), 1)
        self.driver.get(url)
        self.assertRaises(NoSuchElementException, self.driver.find_element_by_class_name, 'cms_toolbar-item_logout')
        username_input = self.driver.find_element_by_id("id_cms-username")
        username_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input = self.driver.find_element_by_id("id_cms-password")
        password_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input.submit()
        self.wait_page_loaded()
        self.assertTrue(self.driver.find_element_by_class_name('cms_toolbar-item-navigation'))

    def test_basic_add_pages(self):
        with SettingsOverride(DEBUG=True):
            User = get_user_model()
            self.assertEqual(Page.objects.all().count(), 0)
            self.assertTrue(User.objects.all().count(), 1)
            driver = self.driver
            driver.get(self.base_url + "/de/")
            driver.find_element_by_id("add-page").click()
            driver.find_element_by_id("id_username").clear()
            driver.find_element_by_id("id_username").send_keys(getattr(self.user, User.USERNAME_FIELD))
            driver.find_element_by_id("id_password").clear()
            driver.find_element_by_id("id_password").send_keys(getattr(self.user, User.USERNAME_FIELD))
            driver.find_element_by_css_selector("input[type=\"submit\"]").click()
            driver.find_element_by_name("_save").click()
            driver.find_element_by_link_text(u"Seite hinzufügen").click()
            driver.find_element_by_id("id_title").clear()
            driver.find_element_by_id("id_title").send_keys("SubPage")
            driver.find_element_by_name("_save").click()

