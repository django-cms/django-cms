from django.core.exceptions import ValidationError


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
    
    def modify(self, request, nodes, namespace, id,  post_cut):
        pass
    
class NavigationNode(object):
    title = None
    url = None
    attr = {}
    namespace = None
    id = None
    parent_id = None
    parent_namespace = None
    parent = None # do not touch
    
    def __init__(self, title, url, id, parent_id=None, parent_namespace=None, attr=None):
        self.children = [] # do not touch
        self.title = title
        self.url = url
        self.id = id
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        if attr:
            self.attr = attr
            
    def __repr__(self):
        return "<Navigation Node: %s>" % str(unicode(self.title))
    
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
    