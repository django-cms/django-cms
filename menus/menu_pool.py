from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.utils.importlib import import_module
from django.utils.translation import get_language
from menus import settings as menus_settings
from menus.exceptions import NamespaceAllreadyRegistered
import copy

def lex_cache_key(key):
    """
    Returns the language and site ID a cache key is related to.
    """
    return key.rsplit('_', 2)[1:]

class MenuPool(object):
    def __init__(self):
        self.menus = {}
        self.modifiers = []
        self.discovered = False
        self.cache_keys = set()
        
    def discover_menus(self):
        if self.discovered:
            return    
        for app in settings.INSTALLED_APPS:
            try:
                import_module('.menu', app)
            except ImportError:
                pass
        from menus.modifiers import register
        register()
        self.discovered = True
        
    def clear(self, site_id=None, language=None):
        def relevance_test(keylang, keysite):
            site_ok = not site_id
            language_ok = not language
            if site_id and (site_id == keysite or site_id == int(keysite)):
                site_ok = True
            if language and language == keylang:
                language_ok = True
            return language_ok and site_ok
        to_be_deleted = []
        for key in self.cache_keys:
            keylang, keysite = lex_cache_key(key)
            if relevance_test(keylang, keysite):
                to_be_deleted.append(key)
        cache.delete_many(to_be_deleted)
        self.cache_keys.difference_update(to_be_deleted)
    
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
        """
        This is slow. Caching must be used. 
        One menu is built per language and per site.
        
        Namespaces: they are ID prefixes to avoid node ID clashes when plugging
        multiple trees together.
        
        - We iterate on the list of nodes.
        - We store encountered nodes in a dict (with namespaces): 
            done_nodes[<namespace>][<node's id>] = node
        - When a node has a parent defined, we lookup that parent in done_nodes
            if it's found:
                set the node as the node's parent's child (re-read this)
            else:
                the node is put at the bottom of the list
        """
        # Cache key management
        lang = get_language()
        prefix = getattr(settings, "CMS_CACHE_PREFIX", "menu_cache_")
        key = "%smenu_nodes_%s_%s" % (prefix, lang, site_id)
        self.cache_keys.add(key)
        
        cached_nodes = cache.get(key, None)
        if cached_nodes:
            return cached_nodes
        
        final_nodes = []
        for menu_class_name in self.menus:
            nodes = self.menus[menu_class_name].get_nodes(request)
            # nodes is a list of navigation nodes (page tree in cms + others)
            final_nodes += self._build_nodes_inner_for_one_menu(nodes, 
                                                                menu_class_name)
        duration = getattr(settings, "MENU_CACHE_DURATION", 60*60)
        cache.set(key, final_nodes, duration)
        return final_nodes
    
    def _build_nodes_inner_for_one_menu(self, nodes, menu_class_name):
        '''
        This is an easier to test "inner loop" building the menu tree structure
        for one menu (one language, one site) 
        '''
        done_nodes = {} # Dict of node.id:Node
        final_nodes = []
        
        # This is to prevent infinite loops - we need to compare the number of 
        # times we see a specific node to "something", and for the time being, 
        # it's the total number of nodes
        list_total_length = len(nodes)
        
        while nodes:
            # For when the node has a parent_id but we haven't seen it yet. 
            # We must not append it to the final list in this case!
            should_add_to_final_list = True 
            
            node = nodes.pop(0)
            
            # Increment the "seen" counter for this specific node.
            node._counter = getattr(node,'_counter',0) + 1  
            
            # Implicit namespacing by menu.__name__
            if not node.namespace:
                node.namespace = menu_class_name
            if node.namespace not in done_nodes:
                # We need to create the namespace dict to avoid KeyErrors
                done_nodes[node.namespace] = {} 
            
            # If we have seen the parent_id already...
            if node.parent_id in done_nodes[node.namespace] :
                # Implicit parent namespace by menu.__name__
                if not node.parent_namespace:
                    node.parent_namespace = menu_class_name
                parent = done_nodes[node.namespace][node.parent_id]
                parent.children.append(node)
                node.parent = parent
            # If it has a parent_id but we haven't seen it yet...
            elif node.parent_id:
                # We check for infinite loops here, by comparing the number of 
                # times we "saw" this node to the number of nodes in the list
                if node._counter < list_total_length:
                    nodes.append(node)
                # Never add this node to the final list until it has a real 
                # parent (node.parent)
                should_add_to_final_list = False
                
            if should_add_to_final_list:
                final_nodes.append(node)
                # add it to the "seen" list
                done_nodes[node.namespace][node.id] = node
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
            if node.get_absolute_url() == request.path[:len(node.get_absolute_url())]:
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
