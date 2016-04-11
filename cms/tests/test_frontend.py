# -*- coding: utf-8 -*-
import os
import sys
from importlib import import_module
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
try:
    from django.utils import unittest
except ImportError:
    import unittest

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.cache import cache
from django.core.urlresolvers import clear_url_caches
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException

from cms.api import create_page
from cms.appresolver import clear_app_resolvers
from cms.models import Page, Placeholder
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.mock import AttributeObject
from cms.utils.conf import get_cms_setting


class FastLogin(object):
    def _fastlogin(self, **credentials):
        session = import_module(settings.SESSION_ENGINE).SessionStore()
        session.save()
        request = AttributeObject(session=session, META={})
        user = authenticate(**credentials)
        login(request, user)
        session.save()

        # We need to "warm up" the webdriver as we can only set cookies on the
        # current domain
        self.driver.get(self.live_server_url)
        # While we don't care about the page fully loading, Django will freak
        # out if we 'abort' this request, so we wait patiently for it to finish
        self.wait_page_loaded()
        self.driver.add_cookie({
            'name': settings.SESSION_COOKIE_NAME,
            'value': session.session_key,
            'path': '/',
            'domain': urlparse(self.live_server_url).hostname
        })
        self.driver.get('{0}/?{1}'.format(
            self.live_server_url,
            get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        ))
        self.wait_page_loaded()


class CMSLiveTests(StaticLiveServerTestCase, CMSTestCase):
    driver = None
    @classmethod
    def setUpClass(cls):
        if os.environ.get('SELENIUM', '') != '':
            #skip selenium tests
            raise unittest.SkipTest("Selenium env is set to 0")
        super(CMSLiveTests, cls).setUpClass()
        cache.clear()
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
        super(CMSLiveTests, cls).tearDownClass()
        if cls.driver:
            cls.driver.quit()

    def tearDown(self):
        super(CMSLiveTests, self).tearDown()
        Page.objects.all().delete() # somehow the sqlite transaction got lost.
        cache.clear()

    def wait_until(self, callback, timeout=10):
        """
        Helper function that blocks the execution of the tests until the
        specified callback returns a value that is not falsy. This function can
        be called, for example, after clicking a link or submitting a form.
        See the other public methods that call this function for more details.
        """
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

    def wait_loaded_id(self, id, timeout=10):
        self.wait_until(
            lambda driver: driver.find_element_by_id(id), timeout
        )

    def wait_loaded_selector(self, selector, timeout=10):
        self.wait_until(
            lambda driver: driver.find_element_by_css_selector(selector),
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

    def reload_urls(self):
        """
         Code borrowed from ApphooksTestCase
        """
        from django.conf import settings

        url_modules = [
            'cms.urls',
            # TODO: Add here intermediary modules which may
            #       include() the 'cms.urls' if it isn't included
            #       directly in the root urlconf.
            # '...',
            'cms.test_utils.project.second_cms_urls_for_apphook_tests',
            'cms.test_utils.project.urls_for_apphook_tests',
            settings.ROOT_URLCONF,
        ]

        clear_app_resolvers()
        clear_url_caches()

        for module in url_modules:
            if module in sys.modules:
                del sys.modules[module]


@override_settings(
    SITE_ID=1,
    CMS_PERMISSION=False,
)
class StaticPlaceholderPermissionTests(FastLogin, CMSLiveTests):
    def setUp(self):
        Site.objects.create(domain='example.org', name='example.org')

        self.page = create_page('Home', 'static.html', 'en', published=True)

        self.base_url = self.live_server_url

        self.user = self._create_user("testuser", is_staff=True)
        self.user.user_permissions = Permission.objects.exclude(codename="edit_static_placeholder")

        self.driver.implicitly_wait(2)

        super(StaticPlaceholderPermissionTests, self).setUp()

    def test_static_placeholders_permissions(self):
        username = getattr(self.user, get_user_model().USERNAME_FIELD)
        password = username
        self._fastlogin(username=username, password=password)

        pk = Placeholder.objects.filter(slot='logo').order_by('id')[0].pk
        placeholder_name = 'cms-placeholder-%s' % pk

        # test static placeholder permission (content of static placeholders is NOT editable)
        self.driver.get('%s/en/?%s' % (self.live_server_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
        self.assertRaises(NoSuchElementException, self.driver.find_element_by_class_name, placeholder_name)

        # update userpermission
        edit_permission = Permission.objects.get(codename="edit_static_placeholder")
        self.user.user_permissions.add( edit_permission )

        # test static placeholder permission (content of static placeholders is editable)
        self.driver.get('%s/en/?%s' % (self.live_server_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
        self.assertTrue(self.driver.find_element_by_class_name(placeholder_name))
