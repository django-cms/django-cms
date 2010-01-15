from django.conf import settings
from menus.exceptions import NamespaceAllreadyRegistered, NoParentFound
from django.contrib.sites.models import Site
import copy


class MenuPool(object):
    def __init__(self):
        self.menus = {}
        self.modifiers = []
        self.discovered = False
        self.nodes = {}
        
        
    def discover_menus(self):
        if self.discovered:
            return
        #import all the modules
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['menu'])
        # get all the modifiers 
        for path in settings.MENU_MODIFIERS:
            class_name = path.split(".")[-1]
            module = __import__(".".join(path.split(".")[:-1]),(),(),(class_name,))
            klass = getattr(module, class_name)
            inst = klass()
            self.modifiers.append(inst)
        self.discovered = True
    
    def register_menu(self, menu, namespace):
        from menus.base import Menu
        assert issubclass(menu, Menu)
        if namespace in self.menus.keys():
            raise NamespaceAllreadyRegistered, "[%s] a menu namespace with this name is already registered" % namespace
        self.menus[namespace] = menu()
    
    def _build_nodes(self, request, site_id):
        lang = request.LANGUAGE_CODE
        
        if not lang in self.nodes:
            self.nodes[lang] = {}
        if not site_id in self.nodes[lang]:
            self.nodes[lang][site_id] = []
        else:
            return self.nodes[lang][site_id]
        for ns in self.menus:
            nodes = self.menus[ns].get_nodes(request)
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
                self.nodes[lang][site_id].append(node)
                last = node
        return self.nodes[lang][site_id]
    
    def _apply_modifiers(self, nodes, request, namespace, root_id):
        self._mark_selected(request, nodes)
        for inst in self.modifiers:
            inst.set_nodes(nodes)
            inst.modify_all(request, nodes, namespace, root_id, False)
        for node in nodes:
            for inst in self.modifiers:
                inst.modify(request, node, namespace, root_id, False)
        return nodes
            
    
    def get_nodes(self, request, namespace=None, root_id=None, site_id=None):
        if not self.discovered:
            self.discover_menus()
        if not site_id:
            site_id = Site.objects.get_current().pk
        nodes = self._build_nodes(request, site_id)
        nodes = copy.deepcopy(nodes)
        nodes = self._apply_modifiers(nodes, request, namespace, root_id)
        return nodes 
    
    def _mark_selected(self, request, nodes):
        for node in nodes:
            node.sibling = False
            node.ancestor = False
            node.descendant = False
            if node.get_absolute_url() == request.path:
                node.selected = True
            else:
                node.selected = False
        return nodes
     
menu_pool = MenuPool()
