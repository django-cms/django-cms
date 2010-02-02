from django.conf import settings
from cms.exceptions import AppAllreadyRegistered

class ApphookPool(object):
    def __init__(self):
        self.apps = {}
        self.discovered = False
        
    def discover_apps(self):
        if self.discovered:
            return
        #import all the modules
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['cms_apps'])
        self.discovered = True
        
    def clear(self):
        self.apps = {}
        self.discovered = False

    def register(self, app):
        from cms.app_base import CMSApp
        assert issubclass(app, CMSApp)
        if app.__name__ in self.apps.keys():
            raise AppAllreadyRegistered, "[%s] an cms app with this name is already registered" % app.__name__
        self.apps[app.__name__] = app
        
    def get_apphooks(self):
        hooks = []
        for app_name in self.apps.keys():
            app = self.apps[app_name]
            hooks.append()
            

apphook_pool = ApphookPool()
