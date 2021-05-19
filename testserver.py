#!/usr/bin/env python
import os
import sys


def noop_gettext(s):
    return s


permission = True
cms_toolbar_edit_on = 'edit'

port = 8000

for arg in sys.argv:
    if arg == '--CMS_PERMISSION=False':
        permission = False

    if arg == '--CMS_TOOLBAR_URL__EDIT_ON=test-edit':
        cms_toolbar_edit_on = 'test-edit'

    if arg.startswith('--port='):
        port = arg.split('=')[1]

gettext = noop_gettext


class DisableMigrations:

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return 'notmigrations'

    def update(self, whatever):
        return True


HELPER_SETTINGS = dict(
    ALLOWED_HOSTS=[u'0.0.0.0', u'localhost'],
    CMS_PERMISSION=permission,
    LANGUAGES=(
        ('en', u'English'),
        ('de', u'Deutsch'),
        ('it', u'Italiano'),
        ('zh-cn', u'Chinese (Simplified)'),
    ),
    LANGUAGE_CODE='en',
    PARLER_LANGUAGES={
        1: (
            {'code': 'en', 'fallbacks': ['de',]},
            {'code': 'de', 'fallbacks': ['en',]},
            {'code': 'it', 'fallbacks': ['en',]},
            {'code': 'zh-cn', 'fallbacks': ['en',]},
        ),
        'default': {
            'fallback': 'en',
            'hide_untranslated': False,
        },
    },
    PARLER_ENABLE_CACHING=False,
    CMS_CACHE_DURATIONS={
        'menus': 0,
        'content': 0,
        'permissions': 0,
    },
    CMS_PAGE_CACHE=False,
    CMS_TOOLBAR_URL__EDIT_ON=cms_toolbar_edit_on,
    # required for integration tests
    LOGIN_URL='/admin/login/?user-login=test',
    CMS_LANGUAGES={
        1: [
            {
                'code': 'en',
                'name': gettext('English'),
                'fallbacks': ['de',],
            },
            {
                'code': 'de',
                'name': gettext('German'),
                'fallbacks': ['en',],
            },
            {
                'code': 'it',
                'name': gettext('Italian'),
                'fallbacks': ['en',],
            },
            {
                'code': 'zh-cn',
                'name': gettext('Chinese Simplified'),
                'fallbacks': ['en',]
            },
        ],
        'default': {
            'fallbacks': ['en', 'de',],
            'redirect_on_fallback': False,
            'public': True,
            'hide_untranslated': False,
        }
    },
    CMS_PLACEHOLDER_CONF={
        'placeholder_content_2': {
            'plugin_modules': {
                'Bootstrap3ButtonCMSPlugin': 'Different Grouper'
            },
            'plugin_labels': {
                'Bootstrap3ButtonCMSPlugin': gettext('Add a link')
            },
        }
    },
    INSTALLED_APPS=[
        'djangocms_text_ckeditor',
        'cms.test_utils.project.pluginapp.plugins.link',
        'cms.test_utils.project.pluginapp.plugins.multicolumn',
        'cms.test_utils.project.pluginapp.plugins.multiwrap',
        'cms.test_utils.project.pluginapp.plugins.style',
        'cms.test_utils.project.pluginapp.plugins.dynamic_js_loading',
        'cms.test_utils.project.placeholderapp',
    ],
    MIDDLEWARE=[
        'cms.middleware.utils.ApphookReloadMiddleware',
        'django.middleware.http.ConditionalGetMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        'cms.middleware.language.LanguageCookieMiddleware',
        'cms.middleware.user.CurrentUserMiddleware',
        'cms.middleware.page.CurrentPageMiddleware',
        'cms.middleware.toolbar.ToolbarMiddleware',
    ],
    TEMPLATE_DIRS=(
        os.path.join(
            os.path.dirname(__file__),
            'cms', 'test_utils', 'project', 'templates', 'integration'),
    ),
    CMS_TEMPLATES=(
        ('fullwidth.html', 'Fullwidth'),
        ('page.html', 'Standard page'),
        ('simple.html', 'Simple page'),
    ),
    MIGRATION_MODULES={
        'auth': None,
        'admin': None,
        'contenttypes': None,
        'sessions': None,
        'sites': None,
        'cms': None,
        'menus': None,
        'djangocms_text_ckeditor': None,
    },
)


def _helper_patch(*args, **kwargs):
    from django.core.management import call_command
    from app_helper import utils

    call_command('migrate', run_syncdb=True)
    utils.create_user('normal', 'normal@normal.normal', 'normal', is_staff=True, base_cms_permissions=True,
            permissions=['view_page'])


def run():
    from app_helper import runner
    from app_helper import utils

    os.environ.setdefault('DATABASE_URL', 'sqlite://localhost/testdb.sqlite')

    # Patch app_helper to create tables
    utils._create_db = _helper_patch

    # we use '.runner()', not '.cms()' nor '.run()' because it does not
    # add 'test' argument implicitly
    runner.runner([sys.argv[0], 'cms', '--cms', 'server', '--bind', '0.0.0.0', '--port', str(port)])


if __name__ == "__main__":
    run()
