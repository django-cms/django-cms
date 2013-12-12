# -*- coding: utf-8 -*-
from cms.api import create_page
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils import unittest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from django.test import LiveServerTestCase
import os


class CMSLiveTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('SELENIUM', '1') == '0':
            #skip selenium tests
            raise unittest.SkipTest("Selenium env is set to 0")
        capabilities = webdriver.DesiredCapabilities.CHROME
        capabilities['version'] = '31'
        capabilities['platform'] = 'OS X 10.9'
        capabilities['name'] = 'django CMS'
        if os.environ.get("TRAVIS_BUILD_NUMBER"):
            capabilities['build'] = [os.environ.get("TRAVIS_BUILD_NUMBER", "")]
            capabilities['tags'] = [os.environ.get("TRAVIS_PYTHON_VERSION", ""), "CI"]
            username = os.environ.get("SAUCE_USERNAME", "")
            access_key = os.environ.get("SAUCE_ACCESS_KEY", "")
            capabilities["tunnel-identifier"] = [os.environ.get("TRAVIS_JOB_NUMBER", "")]
            hub_url = "%s:%s@localhost:4445" % (username, access_key)
            cls.driver = webdriver.Remote(desired_capabilities=capabilities, command_executor="http://%s/wd/hub" % hub_url)
            cls.driver.implicitly_wait(30)
        else:
            cls.driver = webdriver.Firefox()
        super(CMSLiveTests, cls).setUpClass()

    def stop_server(self):
        if hasattr(self, 'server_thread'):
            self.server_thread.join()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super(CMSLiveTests, cls).tearDownClass()

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


class ToolbarBasicTests(CMSLiveTests):
    def setUp(self):
        Site.objects.create(domain='example.org', name='example.org')
        super(ToolbarBasicTests, self).setUp()

    #@skipIf(not WebDriver, 'Selenium not found or Django too old')
    def test_toolbar_login(self):
        create_page('Home', 'simple.html', 'en', published=True).publish()
        user = User()
        user.username = 'admin'
        user.set_password('admin')
        user.is_superuser = user.is_staff = user.is_active = True
        user.save()
        url = '%s/?edit' % self.live_server_url
        self.driver.get(url)
        self.assertRaises(NoSuchElementException, self.driver.find_element_by_class_name, 'cms_toolbar-item_logout')
        username_input = self.driver.find_element_by_id("id_cms-username")
        username_input.send_keys('admin')
        password_input = self.driver.find_element_by_id("id_cms-password")
        password_input.send_keys('admin')
        password_input.submit()
        self.wait_page_loaded()
        self.assertTrue(self.driver.find_element_by_class_name('cms_toolbar-item-navigation'))

