# -*- coding: utf-8 -*-
import warnings


class CMSApp(object):
    _urls = None
    name = None
    menus = []
    app_name = None
    app_config = None
    permissions = True
    exclude_permissions = []

    def __new__(cls):
        """
        We want to bind the CMSapp class to a specific AppHookConfig, but only one at a time
        Checking for the runtime attribute should be a sane fix
        """
        if cls.app_config:
            if getattr(cls.app_config, 'cmsapp', None) and cls.app_config.cmsapp != cls:
                raise RuntimeError(
                    'Only one AppHook per AppHookConfiguration must exists.\n'
                    'AppHook %s already defined for %s AppHookConfig' % (
                        cls.app_config.cmsapp.__name__, cls.app_config.__name__
                    )
                )
            cls.app_config.cmsapp = cls
        # mapping the legacy urls attribute to private attribute
        # and exposing the new API
        if hasattr(cls, 'urls'):
            if not isinstance(cls.urls, property):
                cls._urls = cls.urls
                cls.urls = cls.legacy_urls
        else:
            cls.urls = cls.legacy_urls
        return super(CMSApp, cls).__new__(cls)

    def get_configs(self):
        raise NotImplemented('Configurable AppHooks must implement this method')

    def get_config(self, namespace):
        raise NotImplemented('Configurable AppHooks must implement this method')

    def get_config_add_url(self):
        raise NotImplemented('Configurable AppHooks must implement this method')

    @property
    def legacy_urls(self):
        warnings.warn('Accessing CMSApp.urls directly is deprecated, '
                      'and it will be removed in version 3.5; CMSApp.get_urls method',
                      DeprecationWarning)
        return self._urls

    @legacy_urls.setter
    def urls(self, value):
        self._urls = value

    def get_urls(self, page=None):
        return self._urls
