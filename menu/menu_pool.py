from django.conf import settings
from menu.exceptions import NamespaceAllreadyRegistered
from menu.base import Menu


class MenuPool(object):
    def __init__(self):
        self.menus = {}
        self.modifiers = []
        self.discovered = False
        
    def discover_plugins(self):
        if self.discovered:
            return
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['menu']) 
        self.discovered = True
    
    def register_menu(self, menu, namespace):
        assert issubclass(menu, Menu)
        if namespace in self.menus.keys():
            raise NamespaceAllreadyRegistered, "[%s] a menu namespace with this name is already registered" % namespace
        self.menus[namespace] = menu 
        
    def register_extender(self, menu, namespace, parent_id):
        pass
    
    def register_modifier(self, modifier):
        pass
    
menu_pool = MenuPool()
