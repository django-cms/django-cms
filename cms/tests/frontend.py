# -*- coding: utf-8 -*-
from cms.api import create_page
from cms.models import Page
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.unittest import skipIf

try:
    from selenium.webdriver.firefox.webdriver import WebDriver
    from selenium.common.exceptions import NoSuchElementException
    from django.test import LiveServerTestCase
except ImportError:
    from django.test import TestCase as LiveServerTestCase

    WebDriver = NoSuchElementException = False

try:
    # allow xvfb
    from pyvirtualdisplay import Display
except ImportError:
    Display = None


class CMSLiveTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if Display:
            cls.display = Display(visible=0, size=(800, 600))
            cls.display.start()
        if WebDriver:
            cls.selenium = WebDriver()
        super(CMSLiveTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'selenium'):
            cls.selenium.quit()
        if hasattr(cls, 'display'):
            cls.display.stop()
        super(CMSLiveTests, cls).tearDownClass()

    def tearDown(self):
        super(CMSLiveTests, self).tearDown()
        Page.objects.all().delete() # not 100% sure why this is needed, but it is


    def stop_server(self):
        if hasattr(self, 'server_thread'):
            self.server_thread.join()

    def wait_until(self, callback, timeout=10):
        """
        Helper function that blocks the execution of the tests until the
        specified callback returns a value that is not falsy. This function can
        be called, for example, after clicking a link or submitting a form.
        See the other public methods that call this function for more details.
        """
        from selenium.webdriver.support.wait import WebDriverWait

        WebDriverWait(self.selenium, timeout).until(callback)

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
        self.wait_page_loaded()
        self.assertTrue(self.selenium.find_element_by_class_name('cms_toolbar-item-navigation'))

