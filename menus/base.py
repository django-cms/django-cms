# -*- coding: utf-8 -*-
from django.utils.translation import get_language
from django.utils.encoding import smart_str


class Menu(object):
    namespace = None
    
    def __init__(self):
        if not self.namespace:
            self.namespace = self.__class__.__name__

    def get_nodes(self, request):
        """
        should return a list of NavigationNode instances
        """ 
        raise NotImplementedError
    
class Modifier(object):
    
    def modify(self, request, nodes, namespace, root_id,  post_cut, breadcrumb):
        pass
    
class NavigationNode(object):
    
    def __init__(self, title, url, id, parent_id=None, parent_namespace=None, attr=None, visible=True):
        self.children = [] # do not touch
        self.parent = None # do not touch, code depends on this
        self.namespace = None # TODO: Assert why we need this and above
        self.title = title
        self.url = self._remove_current_root(url)
        self.id = id
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        self.visible = visible
        
        if attr:
            self.attr = attr
        else:
            self.attr = {} # To avoid declaring a dict in defaults...
            
    def __repr__(self):
        return "<Navigation Node: %s>" % smart_str(self.title)
    
    def _remove_current_root(self, url):
        current_root = "/%s/" % get_language()
        if url[:len(current_root)] == current_root:
            url = url[len(current_root) - 1:]
        return url
    
    def get_menu_title(self):
        return self.title
    
    def get_absolute_url(self):
        return self.url
    
    def get_attribute(self, name):
        return self.attr[name]
    
    def get_descendants(self):
        nodes = []
        for node in self.children:
            nodes.append(node)
            nodes += node.get_descendants()
        return nodes

    def get_ancestors(self):
        nodes = []
        if getattr(self, 'parent', None):
            nodes.append(self.parent)
            nodes += self.parent.get_ancestors()
        return nodes