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
            self.app_config.cmsapp = self

    def get_configs(self):
        raise NotImplemented('Configured AppHooks must implement this method')

    def get_config(self, namespace):
        raise NotImplemented('Configured AppHooks must implement this method')

    def get_config_add_url(self):
        raise NotImplemented('Configured AppHooks must implement this method')
