# -*- coding: utf-8 -*-
from cms.plugins.text.models import Text
from django.contrib.auth.models import User
from cms.models import Page, CMSPlugin
from django.core.urlresolvers import clear_url_caches
from cms.test_utils.util.context_managers import SettingsOverride
from django.template import Template
from cms.api import create_page
from cms.test_utils.testcases import SettingsOverrideTestCase, URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PLUGIN_ADD


class TestNoI18N(SettingsOverrideTestCase):
    settings_overrides = {
        'LANGUAGE_CODE': 'en-us',
        'LANGUAGES': None,
        'CMS_LANGUAGES': None,
        'USE_I18N': False,
        'ROOT_URLCONF': 'cms.test_utils.project.urls_no18n',
        'MIDDLEWARE_CLASSES': [
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            #'django.middleware.locale.LocaleMiddleware',
            'django.middleware.doc.XViewMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.transaction.TransactionMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
            #'cms.middleware.language.LanguageCookieMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
        ],
        'TEMPLATE_CONTEXT_PROCESSORS': [
            "django.contrib.auth.context_processors.auth",
            'django.contrib.messages.context_processors.messages',
            #"django.core.context_processors.i18n",
            "django.core.context_processors.debug",
            "django.core.context_processors.request",
            "django.core.context_processors.media",
            'django.core.context_processors.csrf',
            "cms.context_processors.media",
            "sekizai.context_processors.sekizai",
            "django.core.context_processors.static",
        ],
    }

    def setUp(self):
        clear_url_caches()
        super(TestNoI18N, self).setUp()

    def tearDown(self):
        clear_url_caches()

    def test_language_chooser(self):
        # test simple language chooser with default args
        page1 = create_page("home", template="col_two.html", language="en-us", published=True)
        context = self.get_context(path="/")
        del context['request'].LANGUAGE_CODE
        tpl = Template("{% load menu_tags %}{% language_chooser %}")
        tpl.render(context)
        self.assertEqual(len(context['languages']), 1)
        # try a different template and some different args
        tpl = Template("{% load menu_tags %}{% language_chooser 'menu/test_language_chooser.html' %}")
        tpl.render(context)
        self.assertEqual(context['template'], 'menu/test_language_chooser.html')
        tpl = Template("{% load menu_tags %}{% language_chooser 'short' 'menu/test_language_chooser.html' %}")
        tpl.render(context)
        self.assertEqual(context['template'], 'menu/test_language_chooser.html')
        for lang in context['languages']:
            self.assertEqual(*lang)

    def test_page_language_url(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.urls_no18n'):
            page1 = create_page("home", template="col_two.html", language="en-us", published=True)
            path = "/"
            context = self.get_context(path=path)
            del context['request'].LANGUAGE_CODE
            context['request'].urlconf = "cms.test_utils.project.urls_no18n"
            tpl = Template("{%% load menu_tags %%}{%% page_language_url '%s' %%}" % "en-us")
            url = tpl.render(context)
            self.assertEqual(url, "%s" % path)

    def test_url_redirect(self):
        with SettingsOverride(
                ROOT_URLCONF='cms.test_utils.project.urls_no18n',
                USE_I18N=True,
                MIDDLEWARE_CLASSES=[
                    'django.contrib.sessions.middleware.SessionMiddleware',
                    'django.contrib.auth.middleware.AuthenticationMiddleware',
                    'django.contrib.messages.middleware.MessageMiddleware',
                    'django.middleware.csrf.CsrfViewMiddleware',
                    'django.middleware.locale.LocaleMiddleware',
                    'django.middleware.doc.XViewMiddleware',
                    'django.middleware.common.CommonMiddleware',
                    'django.middleware.transaction.TransactionMiddleware',
                    'django.middleware.cache.FetchFromCacheMiddleware',
                    #'cms.middleware.language.LanguageCookieMiddleware',
                    'cms.middleware.user.CurrentUserMiddleware',
                    'cms.middleware.page.CurrentPageMiddleware',
                    'cms.middleware.toolbar.ToolbarMiddleware',
                ],
                CMS_LANGUAGES={1: []},
                LANGUAGES=(('en-us', 'English'),)):
            create_page("home", template="col_two.html", language="en-us", published=True, redirect='/foobar/')
            response = self.client.get('/', follow=False)
            self.assertEqual(response['Location'], 'http://testserver/foobar/')

    def test_plugin_add_edit(self):
        page_data = {
            'title': 'test page 1',
            'slug': 'test-page1',
            'language': "en-us",
            'template': 'nav_playground.html',
            'parent': '',
            'site': 1,
            'pagepermission_set-TOTAL_FORMS': 0,
            'pagepermission_set-INITIAL_FORMS': 0,
            'pagepermission_set-MAX_NUM_FORMS': 0,
            'pagepermission_set-2-TOTAL_FORMS': 0,
            'pagepermission_set-2-INITIAL_FORMS': 0,
            'pagepermission_set-2-MAX_NUM_FORMS': 0
        }
        # required only if user haves can_change_permission
        self.super_user = User(username="test", is_staff=True, is_active=True, is_superuser=True)
        self.super_user.set_password("test")
        self.super_user.save()
        self.client.login(username="test", password="test")
        response = self.client.post(URL_CMS_PAGE_ADD[3:], page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'language': "en-us",
            'placeholder': page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD[3:], plugin_data)
        self.assertEquals(response.status_code, 200)
        created_plugin_id = int(response.content)
        self.assertEquals(created_plugin_id, CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = "%s%s/" % (URL_CMS_PLUGIN_EDIT[3:], created_plugin_id)
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body": "Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.get(pk=created_plugin_id)
        self.assertEquals("Hello World", txt.body)
        # edit body, but click cancel button
        data = {
            "body": "Hello World!!",
            "_cancel": True,
        }
        edit_url = '%s%d/' % (URL_CMS_PLUGIN_EDIT[3:], created_plugin_id)
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)