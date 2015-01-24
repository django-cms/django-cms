# -*- coding: utf-8 -*-
class CMSApp(object):
    name = None
    urls = None
    menus = []
    app_name = None
    app_config = None
    permissions = True
    exclude_permissions = []

    def __init__(self):
        if self.app_config:
            if getattr(self.app_config, 'cmsapp', None):
                raise RuntimeError(
                    'Only one AppHook per AppHookConfiguration must exists.\n'
                    'AppHook %s already defined for %s AppHookConfig' % (
                        self.app_config.cmsapp, self.app_config
                    )
                )
            self.app_config.cmsapp = self

    def get_configs(self):
        raise NotImplemented('Configurable AppHooks must implement this method')

    def get_config(self, namespace):
        raise NotImplemented('Configurable AppHooks must implement this method')

    def get_config_add_url(self):
        raise NotImplemented('Configurable AppHooks must implement this method')
