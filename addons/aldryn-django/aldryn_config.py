# -*- coding: utf-8 -*-
import json
import os
import sys
from aldryn_client import forms

SYSTEM_FIELD_WARNING = 'WARNING: this field is auto-written. Please do not change it here.'


class CachedLoader(list):
    """
    A list subclass to be used for the template loaders option

    This subclass exposes the same interface as a list and allows subsequent
    code to alter the list of template loaders without knowing if it has been
    wrapped by the `django.template.loaders.cached.Loader` loader.

    `uncached_*` methods are available to allow cached-loader-aware code to
    alter the main template loaders.
    """
    loader = 'django.template.loaders.cached.Loader'

    def __init__(self, loaders):
        self._cached_loaders = list(loaders)
        super(CachedLoader, self).__init__([
            (self.loader, self._cached_loaders),
        ])

        methods = ('append', 'extend', 'insert', 'remove',
                   'pop', 'index', 'count')
        for method in methods:
            self.overwrite_method(method)

    def overwrite_method(self, method):
        uncached_method = 'uncached_{}'.format(method)
        setattr(self, uncached_method, getattr(self, method))
        setattr(self, method, getattr(self._cached_loaders, method))


class Form(forms.BaseForm):
    languages = forms.CharField(
        'Languages',
        required=True,
        initial='["en", "de"]',
        help_text=SYSTEM_FIELD_WARNING,
    )
    use_manifeststaticfilesstorage = forms.CheckboxField(
        'Hash static file names',
        required=False,
        initial=False,
        help_text=(
            'Use ManifestStaticFilesStorage to manage static files and set '
            'far-expiry headers. Enabling this option disables autosync for '
            'static files, and can cause deployment and/or 500 errors if a '
            'referenced file is missing. Please ensure that your test server '
            'works with this option enabled before deploying it to the live '
            'site.'
        )
    )
    enable_gis = forms.CheckboxField(
        'Enable django.contrib.gis',
        required=False,
        initial=False,
        help_text=(
            'Enable Geodjango (django.contrib.gis) related functionality.\n'
            'WARNING: Requires postgis (contact support to enable it for your '
            'project). For local development change "postgres:9.4" to '
            '"mdillon/postgis:9.4" in docker-compose.yml and run '
            '"aldryn project up" to re-create the db container.'
        )
    )

    def to_settings(self, data, settings):
        import dj_database_url
        import warnings
        from functools import partial
        from aldryn_addons.utils import boolean_ish, djsenv
        env = partial(djsenv, settings=settings)

        # BASE_DIR should already be set by aldryn-addons
        settings['BASE_DIR'] = env('BASE_DIR', required=True)
        settings['DATA_ROOT'] = env('DATA_ROOT', os.path.join(settings['BASE_DIR'], 'data'))
        settings['SECRET_KEY'] = env('SECRET_KEY', 'this-is-not-very-random')
        settings['DEBUG'] = boolean_ish(env('DEBUG', False))
        settings['ENABLE_SYNCING'] = boolean_ish(
            env('ENABLE_SYNCING', settings['DEBUG']))
        settings['DISABLE_TEMPLATE_CACHE'] = boolean_ish(
            env('DISABLE_TEMPLATE_CACHE', settings['DEBUG']))

        settings['DATABASE_URL'] = env('DATABASE_URL')
        settings['CACHE_URL'] = env('CACHE_URL')
        if env('DJANGO_MODE') == 'build':
            # In build mode we don't have any connected services like db or
            # cache available. So we need to configure those things in a way
            # they can run without real backends.
            settings['DATABASE_URL'] = 'sqlite://:memory:'
            settings['CACHE_URL'] = 'locmem://'

        if not settings['DATABASE_URL']:
            settings['DATABASE_URL'] = 'sqlite:///{}'.format(
                os.path.join(settings['DATA_ROOT'], 'db.sqlite3')
            )
            warnings.warn(
                'no database configured. Falling back to DATABASE_URL={0}'.format(
                    settings['DATABASE_URL']
                ),
                RuntimeWarning,
            )
        if not settings['CACHE_URL']:
            settings['CACHE_URL'] = 'locmem://'
            warnings.warn(
                'no cache configured. Falling back to CACHE_URL={0}'.format(
                    settings['CACHE_URL']
                ),
                RuntimeWarning,
            )

        settings['DATABASES']['default'] = dj_database_url.parse(settings['DATABASE_URL'])

        settings['ROOT_URLCONF'] = env('ROOT_URLCONF', 'urls')
        settings['ADDON_URLS'].append('aldryn_django.urls')
        settings['ADDON_URLS_I18N'].append('aldryn_django.i18n_urls')

        settings['WSGI_APPLICATION'] = 'wsgi.application'

        settings['INSTALLED_APPS'].extend([
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.admin',
            'django.contrib.staticfiles',
            'aldryn_django',
        ])

        if settings['ENABLE_SYNCING'] or settings['DISABLE_TEMPLATE_CACHE']:
            loader_list_class = list
        else:
            loader_list_class = CachedLoader

        settings['TEMPLATES'] = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': env('TEMPLATE_DIRS', [os.path.join(settings['BASE_DIR'], 'templates')], ),
                'OPTIONS': {
                    'debug': boolean_ish(env('TEMPLATE_DEBUG', settings['DEBUG'])),
                    'context_processors': [
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                        'django.core.context_processors.i18n',
                        'django.core.context_processors.debug',
                        'django.core.context_processors.request',
                        'django.core.context_processors.media',
                        'django.core.context_processors.csrf',
                        'django.core.context_processors.tz',
                        'django.core.context_processors.static',
                        'aldryn_django.context_processors.debug',
                    ],
                    'loaders': loader_list_class([
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                        'django.template.loaders.eggs.Loader',
                    ]),
                },
            },
        ]

        settings['MIDDLEWARE_CLASSES'] = [
            'django.contrib.sessions.middleware.SessionMiddleware',
            # 'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.contrib.sites.middleware.CurrentSiteMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            # 'django.middleware.security.SecurityMiddleware',
        ]

        if not env('DISABLE_GZIP'):
            settings['MIDDLEWARE_CLASSES'].insert(
                0, 'django.middleware.gzip.GZipMiddleware')

        settings['SITE_ID'] = env('SITE_ID', 1)

        settings['ADDON_URLS_I18N_LAST'] = 'aldryn_django.urls_redirect'

        self.domain_settings(data, settings, env=env)
        self.security_settings(data, settings, env=env)
        self.server_settings(settings, env=env)
        self.logging_settings(settings, env=env)
        # Order matters, sentry settings rely on logging being configured.
        self.sentry_settings(settings, env=env)
        self.cache_settings(settings, env=env)
        self.storage_settings_for_media(settings, env=env)
        self.storage_settings_for_static(data, settings, env=env)
        self.email_settings(data, settings, env=env)
        self.i18n_settings(data, settings, env=env)
        self.migration_settings(settings, env=env)
        settings['ALDRYN_DJANGO_ENABLE_GIS'] = data['enable_gis']
        if settings['ALDRYN_DJANGO_ENABLE_GIS']:
            self.gis_settings(settings, env=env)
        return settings

    def domain_settings(self, data, settings, env):
        settings['ALLOWED_HOSTS'] = env('ALLOWED_HOSTS', ['localhost', '*'])
        # will take a full config dict from ALDRYN_SITES_DOMAINS if available,
        # otherwise fall back to constructing the dict from DOMAIN,
        # DOMAIN_ALIASES and DOMAIN_REDIRECTS
        domain = env('DOMAIN')
        if domain:
            settings['DOMAIN'] = domain

        domains = env('ALDRYN_SITES_DOMAINS', {})
        if not domains and domain:
            domain_aliases = [
                d.strip()
                for d in env('DOMAIN_ALIASES', '').split(',')
                if d.strip()
            ]
            domain_redirects = [
                d.strip()
                for d in env('DOMAIN_REDIRECTS', '').split(',')
                if d.strip()
            ]
            domains = {
                1: {
                    'name': env('SITE_NAME', ''),
                    'domain': domain,
                    'aliases': domain_aliases,
                    'redirects': domain_redirects,
                },
            }
        settings['ALDRYN_SITES_DOMAINS'] = domains

        # This is ensured again by aldryn-sites, but we already do it here
        # as we need the full list of domains later when configuring
        # media/static serving, before aldryn-sites had a chance to run.
        site_domains = domains.get(settings['SITE_ID'])
        if site_domains:
            settings['ALLOWED_HOSTS'].append(site_domains['domain'])
            settings['ALLOWED_HOSTS'].extend(site_domains['aliases'])
            settings['ALLOWED_HOSTS'].extend(site_domains['redirects'])

        settings['INSTALLED_APPS'].append('aldryn_sites')

        settings['MIDDLEWARE_CLASSES'].insert(
            settings['MIDDLEWARE_CLASSES'].index('django.middleware.common.CommonMiddleware'),
            'aldryn_sites.middleware.SiteMiddleware',
        )

    def security_settings(self, data, settings, env):
        s = settings
        s['SECURE_SSL_REDIRECT'] = env('SECURE_SSL_REDIRECT', None)
        s['SECURE_REDIRECT_EXEMPT'] = env('SECURE_REDIRECT_EXEMPT', [])
        s['SECURE_HSTS_SECONDS'] = env('SECURE_HSTS_SECONDS', 0)
        # SESSION_COOKIE_SECURE is handled by
        #   django.contrib.sessions.middleware.SessionMiddleware
        s['SESSION_COOKIE_SECURE'] = env('SESSION_COOKIE_SECURE', False)
        s['SECURE_PROXY_SSL_HEADER'] = env(
            'SECURE_PROXY_SSL_HEADER',
            ('HTTP_X_FORWARDED_PROTO', 'https')
        )
        # SESSION_COOKIE_HTTPONLY and SECURE_FRAME_DENY must be False for CMS
        # SESSION_COOKIE_HTTPONLY is handled by
        #   django.contrib.sessions.middleware.SessionMiddleware
        s['SESSION_COOKIE_HTTPONLY'] = env('SESSION_COOKIE_HTTPONLY', False)

        s['SECURE_CONTENT_TYPE_NOSNIFF'] = env('SECURE_CONTENT_TYPE_NOSNIFF', False)
        s['SECURE_BROWSER_XSS_FILTER'] = env('SECURE_BROWSER_XSS_FILTER', False)

        s['MIDDLEWARE_CLASSES'].insert(
            s['MIDDLEWARE_CLASSES'].index('aldryn_sites.middleware.SiteMiddleware') + 1,
            'django.middleware.security.SecurityMiddleware',
        )

        # Add the debreach middlewares to counter CRIME/BREACH attacks.
        # We always add it even if the GZipMiddleware is not enabled because
        # we cannot assume that every upstream proxy implements a
        # countermeasure itself.
        s['RANDOM_COMMENT_EXCLUDED_VIEWS'] = set([])
        if 'django.middleware.gzip.GZipMiddleware' in s['MIDDLEWARE_CLASSES']:
            index = s['MIDDLEWARE_CLASSES'].index('django.middleware.gzip.GZipMiddleware') + 1
        else:
            index = 0
        s['MIDDLEWARE_CLASSES'].insert(index, 'aldryn_django.middleware.RandomCommentExclusionMiddleware')
        s['MIDDLEWARE_CLASSES'].insert(index, 'debreach.middleware.RandomCommentMiddleware')
        if 'django.middleware.csrf.CsrfViewMiddleware' in s['MIDDLEWARE_CLASSES']:
            s['MIDDLEWARE_CLASSES'].insert(
                s['MIDDLEWARE_CLASSES'].index('django.middleware.csrf.CsrfViewMiddleware'),
                'debreach.middleware.CSRFCryptMiddleware',
            )

    def server_settings(self, settings, env):
        settings['PORT'] = env('PORT', 80)
        settings['BACKEND_PORT'] = env('BACKEND_PORT', 8000)
        settings['ENABLE_NGINX'] = env('ENABLE_NGINX', False)
        settings['ENABLE_PAGESPEED'] = env(
            'ENABLE_PAGESPEED',
            env('PAGESPEED', False),
        )
        settings['STATICFILES_DEFAULT_MAX_AGE'] = env(
            'STATICFILES_DEFAULT_MAX_AGE',
            # Keep BROWSERCACHE_MAX_AGE for backwards compatibility
            env('BROWSERCACHE_MAX_AGE', 300),
        )
        settings['NGINX_CONF_PATH'] = env('NGINX_CONF_PATH')
        settings['NGINX_PROCFILE_PATH'] = env('NGINX_PROCFILE_PATH')
        settings['PAGESPEED_ADMIN_HTPASSWD_PATH'] = env(
            'PAGESPEED_ADMIN_HTPASSWD_PATH',
            os.path.join(
                os.path.dirname(settings['NGINX_CONF_PATH']),
                'pagespeed_admin.htpasswd',
            )
        )
        settings['PAGESPEED_ADMIN_USER'] = env('PAGESPEED_ADMIN_USER')
        settings['PAGESPEED_ADMIN_PASSWORD'] = env('PAGESPEED_ADMIN_PASSWORD')
        settings['DJANGO_WEB_WORKERS'] = env('DJANGO_WEB_WORKERS', 3)
        settings['DJANGO_WEB_MAX_REQUESTS'] = env('DJANGO_WEB_MAX_REQUESTS', 500)
        settings['DJANGO_WEB_TIMEOUT'] = env('DJANGO_WEB_TIMEOUT', 120)

        # https://docs.djangoproject.com/en/1.8/ref/settings/#use-x-forwarded-host
        settings['USE_X_FORWARDED_HOST'] = env('USE_X_FORWARDED_HOST', False)

    def logging_settings(self, settings, env):
        settings['LOGGING'] = {
            'version': 1,
            'disable_existing_loggers': False,
            'filters': {
                'require_debug_false': {
                    '()': 'django.utils.log.RequireDebugFalse',
                },
                'require_debug_true': {
                    '()': 'django.utils.log.RequireDebugTrue',
                },
            },
            'handlers': {
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'stream': sys.stdout,
                },
                'null': {
                    'class': 'django.utils.log.NullHandler',
                },
            },
            'loggers': {
                '': {
                    'handlers': ['console'],
                    'level': 'INFO',
                },
                'django': {
                    'handlers': ['console'],
                    'level': 'INFO',
                },
                'django.request': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'aldryn': {
                    'handlers': ['console'],
                    'level': 'INFO',
                },
                'py.warnings': {
                    'handlers': ['console'],
                },
            }
        }

    def sentry_settings(self, settings, env):
        sentry_dsn = env('SENTRY_DSN')

        if sentry_dsn:
            settings['INSTALLED_APPS'].append('raven.contrib.django')
            settings['RAVEN_CONFIG'] = {'dsn': sentry_dsn}
            settings['LOGGING']['handlers']['sentry'] = {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            }

    def cache_settings(self, settings, env):
        import django_cache_url
        cache_url = env('CACHE_URL')
        if cache_url:
            settings['CACHES']['default'] = django_cache_url.parse(cache_url)

    def storage_settings_for_media(self, settings, env):
        import yurl
        from aldryn_django.storage import parse_storage_url
        if env('DEFAULT_STORAGE_DSN'):
            settings['DEFAULT_STORAGE_DSN'] = env('DEFAULT_STORAGE_DSN')
        settings['MEDIA_URL'] = env('MEDIA_URL', '/media/')
        if 'DEFAULT_STORAGE_DSN' in settings:
            settings.update(parse_storage_url(settings['DEFAULT_STORAGE_DSN']))
        media_host = yurl.URL(settings['MEDIA_URL']).host
        settings['MEDIA_URL_IS_ON_OTHER_DOMAIN'] = (
            media_host and media_host not in settings['ALLOWED_HOSTS']
        )
        settings['MEDIA_ROOT'] = env('MEDIA_ROOT', os.path.join(settings['DATA_ROOT'], 'media'))
        settings['MEDIA_HEADERS'] = []

        cmds = {}
        if os.path.exists('/usr/bin/pngout'):
            cmds['png'] = '/usr/bin/pngout {filename} {filename}.png -s0 -y -force && mv {filename}.png {filename}'
        if os.path.exists('/usr/bin/jpegoptim'):
            cmds['jpeg'] = '/usr/bin/jpegoptim --max=90 --overwrite --strip-all --all-progressive {filename}'
        if os.path.exists('/usr/bin/gifsicle'):
            cmds['gif'] = '/usr/bin/gifsicle --batch --optimize=2 {filename}'
        settings['THUMBNAIL_OPTIMIZE_COMMAND'] = cmds

    def storage_settings_for_static(self, data, settings, env):
        import yurl
        use_gzip = not env('DISABLE_GZIP')
        use_manifest = data['use_manifeststaticfilesstorage']
        if use_gzip:
            if use_manifest:
                storage = 'aldryn_django.storage.ManifestGZippedStaticFilesStorage'
            else:
                storage = 'aldryn_django.storage.GZippedStaticFilesStorage'
        else:
            if use_manifest:
                storage = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
            else:
                storage = 'django.contrib.staticfiles.storage.StaticFilesStorage'
        settings['STATICFILES_STORAGE'] = storage

        settings['STATIC_URL'] = env('STATIC_URL', '/static/')
        static_host = yurl.URL(settings['STATIC_URL']).host
        settings['STATIC_URL_IS_ON_OTHER_DOMAIN'] = (
            static_host and static_host not in settings['ALLOWED_HOSTS']
        )
        settings['STATIC_ROOT'] = env(
            'STATIC_ROOT',
            os.path.join(settings['BASE_DIR'], 'static_collected'),
        )
        settings['STATIC_HEADERS'] = [
            # Set far-future expiration headers for static files with hashed
            # filenames. Also set cors headers to * for fonts.
            (r'.*\.[0-9a-f]{10,16}\.(eot|ttf|otf|woff)', {
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age={}'.format(3600 * 24 * 365),
            }),
            (r'.*\.[0-9a-f]{10,16}\.[a-z]+', {
                'Cache-Control': 'public, max-age={}'.format(3600 * 24 * 365),
            }),
            # Set default expiration headers for all remaining static files.
            # *Has to be last* as processing stops at the first matching
            # pattern it finds. Also set cors headers to * for fonts.
            (r'.*\.(eot|ttf|otf|woff)', {
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age={}'.format(
                    settings['STATICFILES_DEFAULT_MAX_AGE'],
                ),
            }),
            ('.*', {
                'Cache-Control': 'public, max-age={}'.format(
                    settings['STATICFILES_DEFAULT_MAX_AGE'],
                ),
            }),
        ]
        settings['STATICFILES_DIRS'] = env(
            'STATICFILES_DIRS',
            [os.path.join(settings['BASE_DIR'], 'static')]
        )

    def email_settings(self, data, settings, env):
        import dj_email_url

        email_url = env('EMAIL_URL', '')
        if email_url:
            settings['EMAIL_URL'] = email_url
            settings.update(dj_email_url.parse(email_url))

        from_email = env('DEFAULT_FROM_EMAIL', '')
        if from_email:
            settings['DEFAULT_FROM_EMAIL'] = from_email

        server_email = env('SERVER_EMAIL', '')
        if server_email:
            settings['SERVER_EMAIL'] = server_email

    def i18n_settings(self, data, settings, env):
        settings['ALL_LANGUAGES'] = list(settings['LANGUAGES'])
        settings['ALL_LANGUAGES_DICT'] = dict(settings['ALL_LANGUAGES'])
        languages = json.loads(data['languages'])
        settings['LANGUAGE_CODE'] = languages[0]
        settings['USE_L10N'] = True
        settings['USE_I18N'] = True
        settings['LANGUAGES'] = [
            (code, settings['ALL_LANGUAGES_DICT'][code])
            for code in languages
        ]
        settings['LOCALE_PATHS'] = [
            os.path.join(settings['BASE_DIR'], 'locale'),
        ]

    def time_settings(self, settings, env):
        if env('TIME_ZONE'):
            settings['TIME_ZONE'] = env('TIME_ZONE')

    def migration_settings(self, settings, env):
        from aldryn_django import storage
        from aldryn_addons.utils import boolean_ish

        settings.setdefault('MIGRATION_COMMANDS', [])
        mcmds = settings['MIGRATION_COMMANDS']

        mcmds.append('CACHE_URL="locmem://" python manage.py createcachetable django_dbcache; exit 0')
        mcmds.append('python manage.py migrate --noinput')

        if not boolean_ish(env('DISABLE_S3_MEDIA_HEADERS_UPDATE')):
            if settings['DEFAULT_FILE_STORAGE'] == storage.SCHEMES['s3']:
                mcmds.append('python manage.py aldryn_update_s3_media_headers')

    def gis_settings(self, settings, env):
        settings['DATABASES']['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
        settings['INSTALLED_APPS'].append('django.contrib.gis')
