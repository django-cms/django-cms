from django.core.exceptions import ValidationError


class Menu(object):
    name = None
    cms_enabled = False
    namespace = "main"
    
    def __init__(self):
        if self.cms_enabled and not self.name:
            raise ValidationError("the menu %s is cms_enabled but has no name" % self.__class__.__name__)

    def get_nodes(self, request):
        """
        should return a list of NavigationNode instances
        """ 
        raise NotImplementedError
    
class Modifier(object):
    pre_cut = True
    post_cut = False
    
    def set_nodes(self, nodes):
        self.nodes = nodes
    
    def modify(self, request, nodes, namespace, id,  post_cut):
        pass
    
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
    reverse_id = None
   
    selected = False
    
    def __init__(self, title, url, id, parent_id=None, parent_namespace=None, attr=None, softroot=False, auth_required=False, required_group_id=None, reverse_id=None):
        self.children = [] # do not touch
        self.title = title
        self.url = url
        self.id = id
        self.softroot = softroot
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        self.auth_required = auth_required
        self.required_group_id = required_group_id
        self.reverse_id = reverse_id
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
    