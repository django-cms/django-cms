import warnings

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import autodiscover_modules, import_string
from django.utils.translation import gettext as _

from cms.app_base import CMSApp
from cms.exceptions import AppAlreadyRegistered
from cms.utils.conf import get_cms_setting


class ApphookPool:

    def __init__(self):
        self.apphooks = []
        self.apps = {}
        self.discovered = False

    def clear(self):
        # TODO: remove this method, it's Python, we don't need it.
        self.apphooks = []
        self.apps = {}
        self.discovered = False

    def register(self, app=None, discovering_apps=False):
        # allow use as a decorator
        if app is None:
            return lambda app: self.register(app, discovering_apps)

        if self.apphooks and not discovering_apps:
            return app

        if app.__name__ in self.apps:
            raise AppAlreadyRegistered(
                'A CMS application %r is already registered' % app.__name__
            )

        if not issubclass(app, CMSApp):
            raise ImproperlyConfigured(
                'CMS application must inherit from cms.app_base.CMSApp, but %r does not' % app.__name__
            )

        if not hasattr(app, 'menus') and hasattr(app, 'menu'):
            warnings.warn(
                "You define a 'menu' attribute on CMS application %r, but the 'menus' attribute is empty, "
                "did you make a typo?" % app.__name__
            )

        self.apps[app.__name__] = app()
        return app

    def discover_apps(self):
        self.apphooks = get_cms_setting('APPHOOKS')

        if self.apphooks:
            for path in self.apphooks:
                cls = import_string(path)
                try:
                    self.register(cls, discovering_apps=True)
                except AppAlreadyRegistered:
                    pass

        else:
            autodiscover_modules('cms_apps')

        self.discovered = True

    def get_apphooks(self):
        hooks = []

        if not self.discovered:
            self.discover_apps()

        for app_name in self.apps:
            app = self.apps[app_name]
            if app.get_urls():
                hooks.append((app_name, app.name or app_name))

        # Unfortunately, we lose the ordering since we now have a list of
        # tuples. Let's reorder by app_name:
        hooks = sorted(hooks, key=lambda hook: hook[1])

        return hooks

    def get_apphook(self, app_name):
        if not self.discovered:
            self.discover_apps()

        try:
            return self.apps[app_name]
        except KeyError:
            # deprecated: return apphooks registered in db with urlconf name
            # instead of apphook class name
            for app in self.apps.values():
                if app_name in app.get_urls():
                    return app

        warnings.warn(_('No registered apphook "%r" found') % app_name)
        return None


apphook_pool = ApphookPool()
