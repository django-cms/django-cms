

class Menu(object):
    nodes = []

    def get_nodes(self, request):
        raise NotImplementedError
    
class Modifier(object):
    
    def modify(self, request, nodes, namespace):
        raise NotImplementedError
    
    
class NavigationNode(object):
    title = None
    url = None
    auth_required = False
    required_group_id = None
    attr = {}
    namespace = None
    id = None
    softroot = False
    parent_id = None
    parent_namespace = None
    parent = None # do not touch
    childrens = [] # do not touch
    
    def __init__(self, title, url, namespace, id, parent_id=None, parent_namespace=None, attr=None, softroot=False, auth_required=False, required_group_id=None):
        self.title = title
        self.url = url
        self.id = id
        self.softroot = softroot
        self.namespace = namespace
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        self.auth_required = auth_required
        self.required_group_id = required_group_id 
        if attr:
            self.attr = attr
    
    def get_menu_title(self):
        return self.title
    
    def get_absolute_url(self):
        return self.url
    
    def get_attribute(self, name):
        return self.attr[name]
    