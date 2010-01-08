from django.conf import settings
from menus.exceptions import NamespaceAllreadyRegistered, NoParentFound
import copy


class MenuPool(object):
    def __init__(self):
        self.menus = {}
        self.modifiers = []
        self.discovered = False
        self.nodes = []
        
        
    def discover_menus(self):
        if self.discovered:
            return
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['menu']) 
        self.discovered = True
    
    def register_menu(self, menu, namespace):
        from menus.base import Menu
        assert issubclass(menu, Menu)
        if namespace in self.menus.keys():
            raise NamespaceAllreadyRegistered, "[%s] a menu namespace with this name is already registered" % namespace
        self.menus[namespace] = menu 
    
    def build_nodes(self):
        self.nodes = []
        for ns in self.menus:
            nodes = self.menus[ns].get_nodes()
            last = None
            for node in nodes:
                if node.parent_id:
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
                    if not found:
                        raise NoParentFound, "No parent found for %s" % node.get_menu_title()
                    node.parent.children.append(node)
                last = node
    
    def apply_modifiers(self, nodes, request, root_id):
        final = []
        for path in settings.MENU_MODIFIERS:
            class_name = path.split(".")[-1]
            module = __import__(".".join(path.split(".")[:-1]),(),(),(class_name,))
            klass = getattr(module, class_name)
            inst = klass()
            for node in nodes:
                keep = inst.modify(request, node, root_id)
                if keep:
                    final.append(node)
                else:
                    if node.parent:
                        node.parent.children.remove(node)
                    if node in final:
                        final.remove(node)
        return final
            
    
    def get_nodes(self, request, root_id=None):
        if not self.discovered:
            self.discover_menus()
        nodes = copy.deepcopy(self.nodes)
        nodes = self.apply_modifiers(nodes, request, root_id)
        return self.nodes 
    
    
    
menu_pool = MenuPool()
