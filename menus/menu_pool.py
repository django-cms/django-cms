from django.conf import settings
from menus.exceptions import NamespaceAllreadyRegistered, NoParentFound
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
    
    def build_nodes(self, request):
        lang = request.LANGUAGE_CODE
        if lang in self.nodes:
            return self.nodes[lang]
        else:
            self.nodes[lang] = []
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
                self.nodes[lang].append(node)
                last = node
        return self.nodes[lang]
    
    def apply_modifiers(self, nodes, request, root_id):
        self.mark_selected(request, nodes)
        for inst in self.modifiers:
            inst.set_nodes(nodes)
            inst.modify_all(request, nodes, root_id, False)
        for node in nodes:
            for inst in self.modifiers:
                inst.modify(request, node, root_id, False)
        return nodes
            
    
    def get_nodes(self, request, root_id=None):
        if not self.discovered:
            self.discover_menus()
        nodes = self.build_nodes(request)
        nodes = copy.deepcopy(nodes)
        nodes = self.apply_modifiers(nodes, request, root_id)
        return nodes 
    
    def mark_selected(self, request, nodes):
        for node in nodes:
            if node.get_absolute_url() == request.path:
                node.selected = True
            else:
                node.selected = False
        return nodes
    
    
    
menu_pool = MenuPool()
