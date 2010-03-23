from django.conf import settings
from cms.exceptions import AppAllreadyRegistered
from django.core.exceptions import ImproperlyConfigured

class ApphookPool(object):
    def __init__(self):
        self.apps = {}
        self.discovered = False
        self.block_register = False
        
    def discover_apps(self):
        if self.discovered:
            return
        #import all the modules
        if settings.CMS_APPHOOKS:
            
            for app in settings.CMS_APPHOOKS:
                self.block_register = True
                path = ".".join(app.split(".")[:-1])
                class_name = app.split(".")[-1]
                cls = __import__(path, {}, {}, [class_name])
                self.block_register = False
                self.register(cls)
        else:
            for app in settings.INSTALLED_APPS:
                __import__(app, {}, {}, ['cms_app'])
        self.discovered = True
        
    def clear(self):
        self.apps = {}
        self.discovered = False

    def register(self, app):
        if self.block_register:
            return
        from cms.app_base import CMSApp
        assert issubclass(app, CMSApp)
        if app.__name__ in self.apps.keys():
            raise AppAllreadyRegistered, "[%s] an cms app with this name is already registered" % app.__name__
        self.apps[app.__name__] = app
        
    def get_apphooks(self):
        self.discover_apps()
        hooks = []
        for app_name in self.apps.keys():
            app = self.apps[app_name]
            hooks.append((app_name, app.name))
        return hooks
    
    def get_apphook(self, app_name):
        try:
            return self.apps[app_name]
        except KeyError:
            # deprecated: return apphooks registered in db with urlconf name instead of apphook class name 
            for app in self.apps.values():
                if app_name in app.urls:
                    return app
        raise ImproperlyConfigured('No registered apphook `%s` found.' % app_name)

apphook_pool = ApphookPool()
