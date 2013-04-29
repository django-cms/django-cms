# -*- coding: utf-8 -*-
from django.core.urlresolvers import clear_url_caches
from cms.test_utils.util.context_managers import SettingsOverride
from django.template import Template
from cms.api import create_page
from cms.test_utils.testcases import SettingsOverrideTestCase


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
