from django.contrib.auth import get_user_model
from django.template import Template
from django.test.utils import override_settings
from django.urls import clear_url_caches

from cms.api import create_page
from cms.models import CMSPlugin, Page
from cms.test_utils.testcases import CMSTestCase

overrides = dict(
    LANGUAGE_CODE='en-us',
    LANGUAGES=[],
    CMS_LANGUAGES={},
    USE_I18N=False,
    ROOT_URLCONF='cms.test_utils.project.urls_no18n',
    TEMPLATE_CONTEXT_PROCESSORS=[
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'django.core.context_processors.debug',
        'django.core.context_processors.request',
        'django.core.context_processors.media',
        'django.core.context_processors.csrf',
        'cms.context_processors.cms_settings',
        'sekizai.context_processors.sekizai',
        'django.core.context_processors.static',
    ],
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.cache.FetchFromCacheMiddleware',
        'cms.middleware.user.CurrentUserMiddleware',
        'cms.middleware.page.CurrentPageMiddleware',
        'cms.middleware.toolbar.ToolbarMiddleware',
    ]
)


@override_settings(**overrides)
class TestNoI18N(CMSTestCase):

    def setUp(self):
        clear_url_caches()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        clear_url_caches()

    def test_language_chooser(self):
        # test simple language chooser with default args
        create_page("home", template="col_two.html", language="en-us")
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
            create_page("home", template="col_two.html", language="en-us")
            path = "/"
            context = self.get_context(path=path)
            del context['request'].LANGUAGE_CODE
            context['request'].urlconf = "cms.test_utils.project.urls_no18n"
            tpl = Template("{%% load menu_tags %%}{%% page_language_url '%s' %%}" % "en-us")
            url = tpl.render(context)
            self.assertEqual(url, "%s" % path)

    def test_url_redirect(self):
        overrides = dict(
            USE_I18N=True,
            CMS_LANGUAGES={1: []},
            LANGUAGES=[('en-us', 'English')],
            MIDDLEWARE=[
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
            ]
        )
        with self.settings(**overrides):
            homepage = create_page(
                "home",
                template="col_two.html",
                language="en-us",
                redirect='/foobar/',
            )
            homepage.set_as_homepage()
            response = self.client.get('/', follow=False)
            self.assertTrue(response.status_code, 302)  # Needs to redirect
            self.assertTrue(response['Location'].endswith("/foobar/"))  # to /foobar/

    def test_plugin_add_edit(self):
        page_data = {
            'title': 'test page 1',
            'slug': 'test-page1',
            'language': "en-us",
            'parent': '',
        }
        # required only if user haves can_change_permission
        self.super_user = self._create_user("test", True, True)
        self.client.login(username=getattr(self.super_user, get_user_model().USERNAME_FIELD),
                          password=getattr(self.super_user, get_user_model().USERNAME_FIELD))

        self.client.post(self.get_page_add_uri('en'), page_data)
        page = Page.objects.first()
        self.client.post(self.get_page_change_template_uri('en-us', page)[3:], page_data)
        page = Page.objects.first()
        placeholder = page.get_placeholders("en-us").latest('id')
        data = {'name': 'Hello', 'external_link': 'http://www.example.org/'}
        add_url = self.get_add_plugin_uri(placeholder, 'LinkPlugin', 'en-us')

        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 200)
        created_plugin = CMSPlugin.objects.all()[0]
        # now edit the plugin
        edit_url = self.get_change_plugin_uri(created_plugin)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        data['name'] = 'Hello World'
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        Link = self.get_plugin_model('LinkPlugin')
        link = Link.objects.get(pk=created_plugin.pk)
        self.assertEqual("Hello World", link.name)
