

class Menu(object):
    nodes = []

    def get_nodes(self, request):
        raise NotImplementedError
    
    def get_node_by_id(self, id):
        for node in self.nodes:
            if node.id == id:
                return node
    
class Modifier(object):
    pre_cut = True
    post_cut = False
    
    def set_nodes(self, nodes):
        self.nodes = nodes
    
    def modify(self, request, nodes, namespace, id,  post_cut):
        pass
    
    def modify_all(self, request, nodes, namespace, id, post_cut):
        pass
    
    def remove_node(self, node):
        self.nodes.remove(node)
        if node.parent:
            node.parent.children.remove(node)
    
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
   
    selected = False
    
    def __init__(self, title, url, namespace, id, parent_id=None, parent_namespace=None, attr=None, softroot=False, auth_required=False, required_group_id=None):
        self.children = [] # do not touch
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
            
    def __repr__(self):
        return "<Navigation Node: %s>" % self.title
    
    def get_menu_title(self):
        return self.title
    
    def get_absolute_url(self):
        return self.url
    
    def get_attribute(self, name):
        return self.attr[name]
    