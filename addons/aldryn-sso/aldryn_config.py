# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):
    hide_user_management = forms.CheckboxField(
        'Hide user management',
        required=False,
        initial=False,
    )

    def to_settings(self, data, settings):
        from functools import partial
        from aldryn_addons.exceptions import ImproperlyConfigured
        from aldryn_addons.utils import boolean_ish
        from aldryn_addons.utils import djsenv
        from simple_sso.compat import reverse_lazy

        def boolean_ish_or(value, or_values=()):
            if value in or_values:
                return value
            return boolean_ish(value)

        env = partial(djsenv, settings=settings)

        if settings.get('MIDDLEWARE'):
            # Django>=1.10
            MIDDLEWARE = settings['MIDDLEWARE']
        else:
            # Django<1.10
            MIDDLEWARE = settings['MIDDLEWARE_CLASSES']

        settings['ALDRYN_SSO_HIDE_USER_MANAGEMENT'] = data['hide_user_management']

        # if the SSO button is the only configured login option: redirect right
        # to the login without showing the page.
        settings['ALDRYN_SSO_ENABLE_AUTO_SSO_LOGIN'] = boolean_ish(
            env('ALDRYN_SSO_ENABLE_AUTO_SSO_LOGIN', True)
        )

        settings['SSO_DSN'] = env('SSO_DSN')

        settings['LOGIN_REDIRECT_URL'] = '/'

        settings['ALDRYN_SSO_ENABLE_SSO_LOGIN'] = boolean_ish(
            env(
                'ALDRYN_SSO_ENABLE_SSO_LOGIN',
                default=boolean_ish(settings['SSO_DSN']),
            )
        )

        settings['ALDRYN_SSO_ENABLE_LOGIN_FORM'] = boolean_ish(
            env(
                'ALDRYN_SSO_ENABLE_LOGIN_FORM',
                default=not settings['ALDRYN_SSO_HIDE_USER_MANAGEMENT'],
            )
        )

        settings['ALDRYN_SSO_ENABLE_LOCALDEV'] = boolean_ish(
            env(
                'ALDRYN_SSO_ENABLE_LOCALDEV',
                default=env('STAGE') == 'local',
            )
        )

        settings['ALDRYN_SSO_ALWAYS_REQUIRE_LOGIN'] = boolean_ish_or(
            env(
                'ALDRYN_SSO_ALWAYS_REQUIRE_LOGIN',
                default=env('STAGE') == 'test',
            ),
            or_values=(
                'basicauth',
            )
        )

        settings['ALDRYN_SSO_LOGIN_WHITE_LIST'] = env(
            'ALDRYN_SSO_LOGIN_WHITE_LIST',
            default=[]
        )

        settings['ADDON_URLS'].append('aldryn_sso.urls')
        settings['ADDON_URLS_I18N'].append('aldryn_sso.urls_i18n')

        # aldryn_sso must be after django.contrib.admin so it can unregister
        # the User/Group Admin if necessary.
        settings['INSTALLED_APPS'].insert(
            settings['INSTALLED_APPS'].index('django.contrib.admin'),
            'aldryn_sso'
        )

        if settings['ALDRYN_SSO_ENABLE_SSO_LOGIN']:
            # Expire user session every day because:
            # Users can change their data on the SSO server.
            # We cannot do a sync of "recently changed" user data due to these reasons:
            # - security risk, leaking user data to unauthorized websites,
            # - it would require some periodic tasks (celery?),
            # - stage websites are being paused during which the sync wouldn't work
            settings['CLOUD_USER_SESSION_EXPIRATION'] = 24 * 60 * 60  # 24h = 1day
            if not settings['SSO_DSN']:
                raise ImproperlyConfigured(
                    'ALDRYN_SSO_ENABLE_SSO_LOGIN is True, but no SSO_DSN is set.')
        if settings['ALDRYN_SSO_ALWAYS_REQUIRE_LOGIN'] == 'basicauth':
            basicauth_user = env('ALDRYN_SSO_BASICAUTH_USER')
            basicauth_password = env('ALDRYN_SSO_BASICAUTH_PASSWORD')
            if basicauth_user and basicauth_password:
                settings['ALDRYN_SSO_BASICAUTH_USER'] = basicauth_user
                settings['ALDRYN_SSO_BASICAUTH_PASSWORD'] = basicauth_password
            else:
                raise ImproperlyConfigured(
                    'ALDRYN_SSO_ALWAYS_REQUIRE_LOGIN set to "basicauth", but '
                    'ALDRYN_SSO_BASICAUTH_USER and ALDRYN_SSO_BASICAUTH_PASSWORD not set'
                )
            position = MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1
            MIDDLEWARE.insert(position, 'aldryn_sso.middleware.BasicAuthAccessControlMiddleware')
        elif settings['ALDRYN_SSO_ALWAYS_REQUIRE_LOGIN']:
            position = MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1
            MIDDLEWARE.insert(position, 'aldryn_sso.middleware.AccessControlMiddleware')
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].extend([
                reverse_lazy('simple-sso-login'),
                reverse_lazy('aldryn_sso_login'),
                reverse_lazy('aldryn_sso_localdev_login'),
                reverse_lazy('aldryn_localdev_create_user'),
            ])

        if settings['ALDRYN_SSO_ALWAYS_REQUIRE_LOGIN']:
            settings['SHARING_VIEW_ONLY_TOKEN_KEY_NAME'] = env('SHARING_VIEW_ONLY_TOKEN_KEY_NAME')
            settings['SHARING_VIEW_ONLY_SECRET_TOKEN'] = env('SHARING_VIEW_ONLY_SECRET_TOKEN')

        settings['ALDRYN_SSO_OVERIDE_ADMIN_LOGIN_VIEW'] = env(
            'ALDRYN_SSO_OVERIDE_ADMIN_LOGIN_VIEW',
            any([
                settings['ALDRYN_SSO_ENABLE_SSO_LOGIN'],
                settings['ALDRYN_SSO_ENABLE_LOGIN_FORM'],
                settings['ALDRYN_SSO_ENABLE_LOCALDEV'],
            ])
        )

        if settings['ALDRYN_SSO_OVERIDE_ADMIN_LOGIN_VIEW']:
            # configure our combined login view to be the default
            settings['LOGIN_URL'] = 'aldryn_sso_login'
            # see admin.py for how we force admin to use this view as well
        return settings
