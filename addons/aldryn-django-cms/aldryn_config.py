# -*- coding: utf-8 -*-
import json
import os

from aldryn_client import forms


SYSTEM_FIELD_WARNING = 'WARNING: this field is auto-written. Please do not change it here.'


class Form(forms.BaseForm):
    permissions_enabled = forms.CheckboxField(
        'Enable permission checks',
        required=False,
        initial=True,
        help_text=(
            'When set, provides new fields in each page\'s settings to assign '
            'levels of access to particular users.'
        ),
    )
    cms_templates = forms.CharField(
        'CMS Templates',
        required=True,
        initial='[["default.html", "Default"]]',
        help_text=(
            'A list, in JSON format, of django CMS templates available to the '
            'project. Use double quotes for values. This list will be '
            'overridden if the project supplies a <a href='
            '\'http://docs.django-cms.org/en/stable/reference/configuration.html#cms-templates\''
            'target=\'_blank\'>CMS_TEMPLATES setting</a>. See <a href='
            '\'http://support.divio.com/project-types/django-cms/manage-templates-in-your-django-cms-project-on-the-divio-cloud\' '  # noqa
            'target=\'_blank\'>Manage templates in your django CMS project</a> for more information.'
        ),
    )
    boilerplate_name = forms.CharField(
        'Boilerplate Name',
        required=False,
        initial='',
        help_text=SYSTEM_FIELD_WARNING,
    )
    cms_content_cache_duration = forms.NumberField(
        'Set Cache Duration for Content',
        required=False,
        initial=60,
        help_text=(
            'Cache expiration (in seconds) for show_placeholder, page_url, '
            'placeholder and static_placeholder template tags.'
        ),
    )
    cms_menus_cache_duration = forms.NumberField(
        'Set Cache Duration for Menus',
        required=False,
        initial=3600,
        help_text='Cache expiration (in seconds) for the menu tree.',
    )

    def to_settings(self, data, settings):
        from functools import partial
        from django.urls import reverse_lazy
        from aldryn_addons.utils import djsenv

        env = partial(djsenv, settings=settings)

        # Core CMS stuff
        settings['INSTALLED_APPS'].extend([
            'cms',
            # 'aldryn_django_cms' must be after 'cms', otherwise we get
            # import time exceptions on other packages (e.g alryn-bootstrap3
            # returns:
            # link_page = cms.models.fields.PageField(
            # AttributeError: 'module' object has no attribute 'fields'
            # )
            'aldryn_django_cms',
            'menus',
            'sekizai',
            'treebeard',
        ])

        # TODO: break out this stuff into other addons
        settings['INSTALLED_APPS'].extend([
            'parler',
        ])
        settings['INSTALLED_APPS'].insert(
            settings['INSTALLED_APPS'].index('django.contrib.admin'),
            'djangocms_admin_style',
        )

        settings['TEMPLATES'][0]['OPTIONS']['context_processors'].extend([
            'sekizai.context_processors.sekizai',
            'cms.context_processors.cms_settings',
        ])

        middlewares = [
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'cms.middleware.language.LanguageCookieMiddleware',
        ]

        if settings.get('MIDDLEWARE_CLASSES', None):
            settings['MIDDLEWARE_CLASSES'].extend(middlewares)
            settings['MIDDLEWARE_CLASSES'].insert(0, 'cms.middleware.utils.ApphookReloadMiddleware', )
        else:
            settings['MIDDLEWARE'].extend(middlewares)
            settings['MIDDLEWARE'].insert(0, 'cms.middleware.utils.ApphookReloadMiddleware', )

        settings['ADDON_URLS_I18N_LAST'] = 'cms.urls'

        settings['CMS_PERMISSION'] = data['permissions_enabled']

        cache_durations = settings.setdefault('CMS_CACHE_DURATIONS', {
            'content': 60,
            'menus': 60 * 60,
            'permissions': 60 * 60,
        })

        if data['cms_content_cache_duration']:
            cache_durations['content'] = data['cms_content_cache_duration']

        if data['cms_menus_cache_duration']:
            cache_durations['menus'] = data['cms_menus_cache_duration']

        old_cms_templates_json = os.path.join(settings['BASE_DIR'], 'cms_templates.json')

        if os.path.exists(old_cms_templates_json):
            # Backwards compatibility with v2
            with open(old_cms_templates_json) as fobj:
                templates = json.load(fobj)
        else:
            templates = settings.get('CMS_TEMPLATES', json.loads(data['cms_templates']))

        settings['CMS_TEMPLATES'] = templates

        # languages
        language_codes = [code for code, lang in settings['LANGUAGES']]
        settings['CMS_LANGUAGES'] = {
            'default': {
                'fallbacks': [fbcode for fbcode in language_codes],
                'redirect_on_fallback': True,
                'public': True,
                'hide_untranslated': False,
            },
            1: [
                {
                    'code': code,
                    'name': settings['ALL_LANGUAGES_DICT'][code],
                    'fallbacks': [fbcode for fbcode in language_codes if fbcode != code],
                    'public': True
                } for code in language_codes
            ]
        }

        settings['PARLER_LANGUAGES'] = {}

        for site_id, languages in settings['CMS_LANGUAGES'].items():
            if isinstance(site_id, int):
                langs = [
                    {
                        'code': lang['code'],
                        'fallbacks': [fbcode for fbcode in language_codes if fbcode != lang['code']]
                    } for lang in languages
                ]
                settings['PARLER_LANGUAGES'].update({site_id: langs})

        parler_defaults = {'fallback': settings['LANGUAGE_CODE']}

        for k, v in settings['CMS_LANGUAGES'].get('default', {}).items():
            if k in ['hide_untranslated', ]:
                parler_defaults.update({k: v})

        settings['PARLER_LANGUAGES'].update({'default': parler_defaults})

        # aldryn-boilerplates and aldryn-snake

        # FIXME: Make ALDRYN_BOILERPLATE_NAME a configurable parameter

        settings['ALDRYN_BOILERPLATE_NAME'] = env(
            'ALDRYN_BOILERPLATE_NAME',
            data.get('boilerplate_name', 'legacy'),
        )
        settings['INSTALLED_APPS'].append('aldryn_boilerplates')

        TEMPLATE_CONTEXT_PROCESSORS = settings['TEMPLATES'][0]['OPTIONS']['context_processors']
        TEMPLATE_LOADERS = settings['TEMPLATES'][0]['OPTIONS']['loaders']
        TEMPLATE_CONTEXT_PROCESSORS.extend([
            'aldryn_boilerplates.context_processors.boilerplate',
            'aldryn_snake.template_api.template_processor',
        ])
        TEMPLATE_LOADERS.insert(
            TEMPLATE_LOADERS.index('django.template.loaders.app_directories.Loader'),
            'aldryn_boilerplates.template_loaders.AppDirectoriesLoader'
        )

        settings['STATICFILES_FINDERS'].insert(
            settings['STATICFILES_FINDERS'].index('django.contrib.staticfiles.finders.AppDirectoriesFinder'),
            'aldryn_boilerplates.staticfile_finders.AppDirectoriesFinder',
        )

        # django sitemap support
        settings['INSTALLED_APPS'].append('django.contrib.sitemaps')

        # django-compressor
        settings['INSTALLED_APPS'].append('compressor')
        settings['STATICFILES_FINDERS'].append('compressor.finders.CompressorFinder')
        # Disable django-comporessor for now. It does not work with the current
        # setup. The cache is shared, which holds the manifest. But the
        # compressed files reside in the docker container, which can go away at
        # any time.
        # Working solutions could be:
        # 1) use pre-compression
        # (https://django-compressor.readthedocs.org/en/latest/usage/#pre-compression)
        # at docker image build time.
        # 2) Use shared storage and save the manifest with the generated files.
        # Although that could be a problem if different versions of the same
        # app compete for the manifest file.

        # We're keeping compressor in INSTALLED_APPS for now, so that templates
        # in existing projects don't break.
        settings['COMPRESS_ENABLED'] = env('COMPRESS_ENABLED', False)

        if settings['COMPRESS_ENABLED']:
            # Set far-future expiration headers for django-compressor
            # generated files.
            settings.setdefault('STATIC_HEADERS', []).insert(0, (
                r'{}/.*'.format(settings.get('COMPRESS_OUTPUT_DIR', 'CACHE')),
                {
                    'Cache-Control': 'public, max-age={}'.format(86400 * 365),
                },
            ))

        # django-robots
        settings['INSTALLED_APPS'].append('robots')

        settings['MIGRATION_COMMANDS'].append(
            'python manage.py cms fix-tree'
        )

        # default plugins
        settings['INSTALLED_APPS'].extend([
            # required by aldryn-forms
            'captcha',
        ])

        # select2 (required by djangocms_link plugin)
        settings['INSTALLED_APPS'].extend([
            'django_select2',
        ])

        settings['ADDON_URLS'].append('aldryn_django_cms.urls')
        settings['ADDON_URLS_I18N'].append('aldryn_django_cms.urls_i18n')

        if 'ALDRYN_SSO_LOGIN_WHITE_LIST' in settings:
            # stage sso enabled
            # add internal endpoints that do not require authentication
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].append(reverse_lazy('cms-check-uninstall'))
            # this is an internal django-cms url
            # which gets called when a user logs out from toolbar
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].append(reverse_lazy('admin:cms_page_resolve'))

        # Prevent injecting random comments to counter BREACH/CRIME attacks
        # into the page tree snippets, as the javascript parsing the result
        # expects a single top-level element.
        (settings
         .setdefault('RANDOM_COMMENT_EXCLUDED_VIEWS', set([]))
         .add('cms.admin.pageadmin.get_tree'))

        return settings
