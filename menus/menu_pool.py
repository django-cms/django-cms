from django.conf import settings
from menus.exceptions import NamespaceAllreadyRegistered, NoParentFound
from django.contrib.sites.models import Site
import copy
from django.core.cache import cache
import pickle

class MenuPool(object):
    def __init__(self):
        self.menus = {}
        self.modifiers = []
        self.discovered = False
        
    def discover_menus(self):
        if self.discovered:
            return    
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['menu'])
        from menus.modifiers import register
        register()
        self.discovered = True
        
    def clear(self, site_id):
        for lang in dict(settings.CMS_LANGUAGES).keys():
            key = "menu_nodes_%s_%s" % (lang, site_id)
            cache.delete(key)
    
    def register_menu(self, menu):
        from menus.base import Menu
        assert issubclass(menu, Menu)
        if menu.__name__ in self.menus.keys():
            raise NamespaceAllreadyRegistered, "[%s] a menu with this name is already registered" % menu.__name__
        self.menus[menu.__name__] = menu()
        
    def register_modifier(self, modifier_class):
        from menus.base import Modifier
        assert issubclass(modifier_class, Modifier)
        if not modifier_class in self.modifiers:
            self.modifiers.append(modifier_class)
        
    
    def _build_nodes(self, request, site_id):
        lang = request.LANGUAGE_CODE
        key = "menu_nodes_%s_%s" % (lang, site_id)
        cached_nodes = cache.get(key, None)
        if cached_nodes:
            return cached_nodes
        final_nodes = []
        for ns in self.menus:
            try:
                nodes = self.menus[ns].get_nodes(request)
            except:
                raise
            last = None
            for node in nodes:
                if not node.namespace:
                    node.namespace = ns
                if node.parent_id:
                    if not node.parent_namespace:
                        node.parent_namespace = ns
                    found = False
                    if last:
                        n = last
                        while n:
                            if n.namespace == node.namespace and n.id == node.parent_id:
                                node.parent = n
                                found = True
                                n = None
                            elif n.parent:
                                n = n.parent
                            else:
                                n = None
                    if not found:
                        for n in nodes:
                            if n.namespace == node.namespace and n.id == node.parent_id:
                                node.parent = n
                                found = True
                    if found:
                        node.parent.children.append(node)
                    else:
                        continue
                final_nodes.append(node)
                last = node
        cache.set(key, final_nodes, 60*60)
        return final_nodes
    
    def apply_modifiers(self, nodes, request, namespace=None, root_id=None, post_cut=False, breadcrumb=False):
        if not post_cut:
            nodes = self._mark_selected(request, nodes)
        for cls in self.modifiers:
            inst = cls()
            nodes = inst.modify(request, nodes, namespace, root_id, post_cut, breadcrumb)
        return nodes
            
    
    def get_nodes(self, request, namespace=None, root_id=None, site_id=None, breadcrumb=False):
        self.discover_menus()
        if not site_id:
            site_id = Site.objects.get_current().pk
        nodes = self._build_nodes(request, site_id)
        nodes = copy.deepcopy(nodes)
        nodes = self.apply_modifiers(nodes, request, namespace, root_id, post_cut=False, breadcrumb=breadcrumb)
        return nodes 
    
    def _mark_selected(self, request, nodes):
        sel = None
        for node in nodes:
            node.sibling = False
            node.ancestor = False
            node.descendant = False
            node.selected = False
            if node.get_absolute_url() == request.path[:len(node.get_absolute_url())] and node.visible:
                if sel:
                    if len(node.get_absolute_url()) > len(sel.get_absolute_url()):
                        sel = node
                else:
                    sel = node
            else:
                node.selected = False
        if sel:
            sel.selected = True
        return nodes
    
    def get_menus_by_attribute(self, name, value):
        self.discover_menus()
        found = []
        for menu in self.menus.items():
            if hasattr(menu[1], name) and getattr(menu[1], name, None) == value:
                found.append((menu[0], menu[1].name))
        return found
    
    def get_nodes_by_attribute(self, nodes, name, value):
        found = []
        for node in nodes:
            if node.attr.get(name, None) == value:
                found.append(node)
        return found
     
menu_pool = MenuPool()
