# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.urlresolvers import clear_url_caches
from django.template import Template
from django.utils.http import urlencode
from django.test import RequestFactory
from django.test.utils import override_settings

from djangocms_text_ckeditor.models import Text

from cms.api import create_page
from cms.middleware.toolbar import ToolbarMiddleware
from cms.models import Page, CMSPlugin
from cms.test_utils.testcases import (CMSTestCase,
                                      URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_EDIT,
                                      URL_CMS_PLUGIN_ADD,
                                      URL_CMS_PAGE_CHANGE_TEMPLATE)
from cms.toolbar.toolbar import CMSToolbar
from cms.utils import get_cms_setting


@override_settings(
    LANGUAGE_CODE='en-us',
    LANGUAGES=[],
    CMS_LANGUAGES={},
    USE_I18N=False,
    ROOT_URLCONF='cms.test_utils.project.urls_no18n',
    MIDDLEWARE_CLASSES=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.cache.FetchFromCacheMiddleware',
        'cms.middleware.user.CurrentUserMiddleware',
        'cms.middleware.page.CurrentPageMiddleware',
        'cms.middleware.toolbar.ToolbarMiddleware',
    ],
    TEMPLATE_CONTEXT_PROCESSORS=[
        "django.contrib.auth.context_processors.auth",
        'django.contrib.messages.context_processors.messages',
        "django.core.context_processors.debug",
        "django.core.context_processors.request",
        "django.core.context_processors.media",
        'django.core.context_processors.csrf',
        "cms.context_processors.cms_settings",
        "sekizai.context_processors.sekizai",
        "django.core.context_processors.static",
    ],
)
class TestNoI18N(CMSTestCase):

    def setUp(self):
        clear_url_caches()
        super(TestNoI18N, self).setUp()

    def tearDown(self):
        super(TestNoI18N, self).tearDown()
        clear_url_caches()

    def get_page_request(self, page, user, path=None, edit=False, lang_code='en', disable=False):
        path = path or page and page.get_absolute_url()
        if edit:
            path += '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.LANGUAGE_CODE = lang_code
        if edit:
            request.GET = {'edit': None}
        else:
            request.GET = {'edit_off': None}
        if disable:
            request.GET[get_cms_setting('CMS_TOOLBAR_URL__DISABLE')] = None
        request.current_page = page
        mid = ToolbarMiddleware()
        mid.process_request(request)
        if hasattr(request, 'toolbar'):
            request.toolbar.populate()
        return request

    def test_language_chooser(self):
        # test simple language chooser with default args
        create_page("home", template="col_two.html", language="en-us", published=True)
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
        with self.settings(ROOT_URLCONF='cms.test_utils.project.urls_no18n'):
            create_page("home", template="col_two.html", language="en-us", published=True)
            path = "/"
            context = self.get_context(path=path)
            del context['request'].LANGUAGE_CODE
            context['request'].urlconf = "cms.test_utils.project.urls_no18n"
            tpl = Template("{%% load menu_tags %%}{%% page_language_url '%s' %%}" % "en-us")
            url = tpl.render(context)
            self.assertEqual(url, "%s" % path)

    def test_url_redirect(self):
        with self.settings(
            USE_I18N=True,
            MIDDLEWARE_CLASSES=[
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.middleware.locale.LocaleMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.cache.FetchFromCacheMiddleware',
                'cms.middleware.user.CurrentUserMiddleware',
                'cms.middleware.page.CurrentPageMiddleware',
                'cms.middleware.toolbar.ToolbarMiddleware',
            ],
            CMS_LANGUAGES={1: []},
            LANGUAGES=[('en-us', 'English')],
        ):
            create_page("home", template="col_two.html", language="en-us", published=True, redirect='/foobar/')
            response = self.client.get('/', follow=False)
            self.assertTrue(response['Location'].endswith("/foobar/"))

    def test_plugin_add_edit(self):
        page_data = {
            'title': 'test page 1',
            'slug': 'test-page1',
            'language': "en-us",
            'template': 'nav_playground.html',
            'parent': '',
            'site': 1,
        }
        # required only if user haves can_change_permission
        self.super_user = self._create_user("test", True, True)
        self.client.login(username=getattr(self.super_user, get_user_model().USERNAME_FIELD),
                          password=getattr(self.super_user, get_user_model().USERNAME_FIELD))

        self.client.post(URL_CMS_PAGE_ADD[3:], page_data)
        page = Page.objects.all()[0]
        self.client.post(URL_CMS_PAGE_CHANGE_TEMPLATE[3:] % page.pk, page_data)
        page = Page.objects.all()[0]

        get_params = {
            'plugin_type': "TextPlugin",
            'plugin_language': "en-us",
            'placeholder_id': page.placeholders.get(slot="body").pk,
        }
        data = {}
        add_url = URL_CMS_PLUGIN_ADD[3:] + '?' + urlencode(
            get_params
        )
        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 302)
        created_plugin_id = CMSPlugin.objects.all()[0].pk
        # now edit the plugin
        edit_url = "%s%s/" % (URL_CMS_PLUGIN_EDIT[3:], created_plugin_id)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        data = {
            "body": "Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        txt = Text.objects.get(pk=created_plugin_id)
        self.assertEqual("Hello World", txt.body)

    def test_toolbar_no_locale(self):
        page = create_page('test', 'nav_playground.html', 'en-us', published=True)
        sub = create_page('sub', 'nav_playground.html', 'en-us', published=True, parent=page)
        # loads the urlconf before reverse below
        sub.get_absolute_url('en-us')
        request = self.get_page_request(sub, self.get_superuser(), edit=True)
        del request.LANGUAGE_CODE
        toolbar = CMSToolbar(request)
        toolbar.set_object(sub)
        self.assertEqual(toolbar.get_object_public_url(), '/sub/')
