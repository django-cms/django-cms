# -*- coding: utf-8 -*-
import datetime
from distutils.version import LooseVersion
import os
import sys
import time
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
try:
    from django.utils import unittest
except ImportError:
    import unittest

import django
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.urlresolvers import clear_url_caches
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException

from cms.api import create_page, create_title, add_plugin
from cms.appresolver import clear_app_resolvers
from cms.apphook_pool import apphook_pool
from cms.exceptions import AppAlreadyRegistered
from cms.models import CMSPlugin, Page, Placeholder
from cms.test_utils.project.placeholderapp.cms_apps import Example1App
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.mock import AttributeObject
from cms.utils.compat import DJANGO_1_6
from cms.utils.conf import get_cms_setting
from cms.utils.django_load import import_module

if DJANGO_1_6:
    from django.test import LiveServerTestCase as StaticLiveServerTestCase
else:
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase


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


class ToolbarBasicTests(CMSLiveTests):
    def setUp(self):
        self.user = self.get_superuser()
        Site.objects.create(domain='example.org', name='example.org')
        self.base_url = self.live_server_url
        self.driver.implicitly_wait(2)
        super(ToolbarBasicTests, self).setUp()

    def test_toolbar_login(self):
        User = get_user_model()
        create_page('Home', 'simple.html', 'en', published=True)
        url = '%s/?%s' % (self.live_server_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertTrue(User.objects.all().count(), 1)
        self.driver.get(url)
        self.assertRaises(NoSuchElementException, self.driver.find_element_by_class_name, 'cms-toolbar-item-logout')
        username_input = self.driver.find_element_by_id("id_cms-username")
        username_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input = self.driver.find_element_by_id("id_cms-password")
        password_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input.submit()
        self.wait_page_loaded()
        self.assertTrue(self.driver.find_element_by_class_name('cms-toolbar-item-navigation'))

    def test_toolbar_login_view(self):
        User = get_user_model()
        create_page('Home', 'simple.html', 'en', published=True)
        ex1 = Example1.objects.create(
            char_1='char_1', char_2='char_1', char_3='char_3', char_4='char_4',
            date_field=datetime.datetime.now()
        )
        try:
            apphook_pool.register(Example1App)
        except AppAlreadyRegistered:
            pass
        self.reload_urls()
        create_page('apphook', 'simple.html', 'en', published=True,
                    apphook=Example1App)


        url = '%s/%s/?%s' % (self.live_server_url, 'apphook/detail/%s' % ex1.pk, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.driver.get(url)
        username_input = self.driver.find_element_by_id("id_cms-username")
        username_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input = self.driver.find_element_by_id("id_cms-password")
        password_input.send_keys("what")
        password_input.submit()
        self.wait_page_loaded()
        self.assertTrue(self.driver.find_element_by_class_name('cms-error'))

    def test_toolbar_login_cbv(self):
        User = get_user_model()
        try:
            apphook_pool.register(Example1App)
        except AppAlreadyRegistered:
            pass
        self.reload_urls()
        create_page('Home', 'simple.html', 'en', published=True)
        ex1 = Example1.objects.create(
            char_1='char_1', char_2='char_1', char_3='char_3', char_4='char_4',
            date_field=datetime.datetime.now()
        )
        create_page('apphook', 'simple.html', 'en', published=True,
                    apphook=Example1App)
        url = '%s/%s/?%s' % (self.live_server_url, 'apphook/detail/class/%s' % ex1.pk, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.driver.get(url)
        username_input = self.driver.find_element_by_id("id_cms-username")
        username_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input = self.driver.find_element_by_id("id_cms-password")
        password_input.send_keys("what")
        password_input.submit()
        self.wait_page_loaded()
        self.assertTrue(self.driver.find_element_by_class_name('cms-error'))


@override_settings(
    LANGUAGE_CODE='en',
    LANGUAGES=(('en', 'English'),
               ('it', 'Italian')),
    CMS_LANGUAGES={
        1: [{'code' : 'en',
             'name': 'English',
             'public': True},
            {'code': 'it',
             'name': 'Italian',
             'public': True},
        ],
        'default': {
            'public': True,
            'hide_untranslated': False,
        },
    },
    SITE_ID=1,
)
class PlaceholderBasicTests(FastLogin, CMSLiveTests):
    def setUp(self):
        Site.objects.create(domain='example.org', name='example.org')

        self.page = create_page('Home', 'simple.html', 'en', published=True)
        self.italian_title = create_title('it', 'Home italian', self.page)

        self.placeholder = self.page.placeholders.all()[0]

        add_plugin(self.placeholder, 'TextPlugin', 'en', body='test')

        self.base_url = self.live_server_url

        self.user = self._create_user('admin', True, True, True)

        self.driver.implicitly_wait(5)

        super(PlaceholderBasicTests, self).setUp()

    def _login(self):
        username = getattr(self.user, get_user_model().USERNAME_FIELD)
        password = username
        self._fastlogin(username=username, password=password)

    def test_copy_from_language(self):
        self._login()
        self.driver.get('%s/it/?%s' % (self.live_server_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))

        # check if there are no plugins in italian version of the page

        italian_plugins = self.page.placeholders.all()[0].get_plugins_list('it')
        self.assertEqual(len(italian_plugins), 0)

        build_button = self.driver.find_element_by_css_selector('.cms-toolbar-item-cms-mode-switcher a[href="?%s"]' % get_cms_setting('CMS_TOOLBAR_URL__BUILD'))
        build_button.click()

        submenu = self.driver.find_element_by_css_selector('.cms-dragbar .cms-submenu-settings')
        submenu.click()

        submenu_link_selector = '.cms-submenu-item a[data-rel="copy-lang"][data-language="en"]'
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, submenu_link_selector)))
        copy_from_english = self.driver.find_element_by_css_selector(submenu_link_selector)
        copy_from_english.click()

        # Done, check if the text plugin was copied and it is only one

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.cms-draggable:nth-child(2)')))

        italian_plugins = self.page.placeholders.all()[0].get_plugins_list('it')
        self.assertEqual(len(italian_plugins), 1)

        plugin_instance = italian_plugins[0].get_plugin_instance()[0]

        self.assertEqual(plugin_instance.body, 'test')

    def test_copy_to_from_clipboard(self):
        self.assertEqual(CMSPlugin.objects.count(), 1)
        self._login()

        build_button = self.driver.find_element_by_css_selector('.cms-toolbar-item-cms-mode-switcher a[href="?%s"]' % get_cms_setting('CMS_TOOLBAR_URL__BUILD'))
        build_button.click()

        cms_draggable = self.driver.find_element_by_css_selector('.cms-dragarea-1 .cms-draggable')

        hov = ActionChains(self.driver).move_to_element(cms_draggable)
        hov.perform()

        submenu = cms_draggable.find_element_by_css_selector('.cms-submenu-settings')
        submenu.click()

        copy = cms_draggable.find_element_by_css_selector('.cms-submenu-dropdown a[data-rel="copy"]')
        copy.click()

        menu_trigger = self.driver.find_element_by_css_selector('.cms-toolbar-left .cms-toolbar-item-navigation li:first-child')

        menu_trigger.click()

        self.driver.find_element_by_css_selector('.cms-clipboard-trigger a').click()

        # necessary sleeps for making a "real" drag and drop, that works with the clipboard
        time.sleep(0.3)

        self.assertEqual(CMSPlugin.objects.count(), 2)

        drag = ActionChains(self.driver).click_and_hold(
            self.driver.find_element_by_css_selector('.cms-clipboard-containers .cms-draggable:nth-child(1)')
        )

        drag.perform()

        time.sleep(0.1)

        drag = ActionChains(self.driver).move_to_element(
            self.driver.find_element_by_css_selector('.cms-dragarea-1')
        )
        drag.perform()

        time.sleep(0.2)

        drag = ActionChains(self.driver).move_by_offset(
            0, 10
        ).release()

        drag.perform()

        time.sleep(0.5)

        self.assertEqual(CMSPlugin.objects.count(), 3)

        plugins = self.page.placeholders.all()[0].get_plugins_list('en')

        self.assertEqual(len(plugins), 2)


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


class FrontAdminTest(CMSLiveTests):

    def setUp(self):
        self.user = self.get_superuser()
        Site.objects.create(domain='example.org', name='example.org')
        self.base_url = self.live_server_url
        self.driver.implicitly_wait(2)
        super(FrontAdminTest, self).setUp()

    @unittest.skipIf(LooseVersion(django.get_version()) >= LooseVersion('1.7'),
                     reason='test not supported in Django 1.7+')
    def test_cms_modal_html5_validation_error(self):
        User = get_user_model()
        try:
            apphook_pool.register(Example1App)
        except AppAlreadyRegistered:
            pass
        self.reload_urls()
        create_page('Home', 'simple.html', 'fr', published=True)
        ex1 = Example1.objects.create(
            char_1='char_1', char_2='char_1', char_3='char_3', char_4='char_4',
            date_field=datetime.datetime.now()
        )
        create_page('apphook', 'simple.html', 'fr', published=True,
                    apphook=Example1App)
        url = '%s/%s/?%s' % (
            self.live_server_url, 'fr/apphook/detail/class/%s'
            % ex1.pk, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
            )
        self.driver.get(url)
        username_input = self.driver.find_element_by_id("id_cms-username")
        username_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input = self.driver.find_element_by_id("id_cms-password")
        password_input.send_keys(getattr(self.user, User.USERNAME_FIELD))
        password_input.submit()
        self.wait_page_loaded()

        # Load modal iframe
        add_button = self.driver.find_element_by_css_selector(
            '.cms-plugin-placeholderapp-example1-add-0'
            )
        open_modal_actions = ActionChains(self.driver)
        open_modal_actions.double_click(add_button)
        open_modal_actions.perform()
        WebDriverWait(self.driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe'))
            )
        # Fills form with an html5 error
        char_1_input = self.driver.find_element_by_id("id_char_1")
        char_1_input.send_keys("test")
        char_2_input = self.driver.find_element_by_id("id_char_2")
        char_2_input.send_keys("test")
        char_3_input = self.driver.find_element_by_id("id_char_3")
        char_3_input.send_keys("test")
        char_4_input = self.driver.find_element_by_id("id_char_4")
        char_4_input.send_keys("test")
        id_date_input = self.driver.find_element_by_id("id_date_field")
        id_date_input.send_keys('2036-01-01')
        id_decimal_input = self.driver.find_element_by_id("id_decimal_field")
        id_decimal_input.send_keys('t')

        self.driver.switch_to_default_content()
        submit_button = self.driver.find_element_by_css_selector('.default')
        submit_button.click()

        # check if the iframe is still displayed because of the html5 error
        modal_iframe = self.driver.find_element_by_css_selector('iframe')
        self.assertTrue(modal_iframe.is_displayed())

        # corrects html5 error
        self.driver.switch_to_frame(modal_iframe)
        id_decimal_input = self.driver.find_element_by_id("id_decimal_field")
        id_decimal_input.send_keys(Keys.BACK_SPACE + '1.2')
        self.driver.switch_to_default_content()
        submit_button = self.driver.find_element_by_css_selector('.default')
        submit_button.click()
        time.sleep(10)
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element_by_css_selector('iframe')
        example = Example1.objects.get(char_1='test')
        self.assertEqual(float(example.decimal_field), 1.2)
