

class Menu(object):
    nodes = []
    
    def add_nodes(self, nodes):
        self.nodes.append(nodes)

    def get_nodes(self, request):
        raise NotImplementedError
    
class Modifier(object):
    
    def modify(self, request, nodes, namespace):
        raise NotImplementedError
    
    
class NavigationNode(object):
    title = None
    url = None
    attr = {}
    namespace = None
    id = None
    softroot = False

    def __init__(self, title, url, namespace, id, attr=None, softroot=False):
        self.title = title
        self.url = url
        self.id = id
        self.softroot = softroot
        self.namespace = namespace
        if attr:
            self.attr = attr
    
    def get_menu_title(self):
        return self.title
    
    def get_absolute_url(self):
        return self.url
    
    def get_attribute(self, name):
        return self.attr[name]
    