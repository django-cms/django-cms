# -*- coding: utf-8 -*-
from django.utils.encoding import smart_str


class Menu(object):
    namespace = None

    def __init__(self, renderer):
        self.renderer = renderer

        if not self.namespace:
            self.namespace = self.__class__.__name__

    def get_nodes(self, request):
        """
        should return a list of NavigationNode instances
        """
        raise NotImplementedError


class Modifier(object):

    def __init__(self, renderer):
        self.renderer = renderer

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        pass


class NavigationNode(object):

    selected = None
    sibling = False
    ancestor = False
    descendant = False

    def __init__(self, title, url, id, parent_id=None, parent_namespace=None,
                 attr=None, visible=True):
        self.children = []  # do not touch
        self.parent = None  # do not touch, code depends on this
        self.namespace = None  # TODO: Assert why we need this and above
        self.title = title
        self.url = url
        self.id = id
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        self.visible = visible
        self.attr = attr or {} # To avoid declaring a dict in defaults...

    def __repr__(self):
        return "<Navigation Node: %s>" % smart_str(self.title)

    def get_menu_title(self):
        return self.title

    def get_absolute_url(self):
        return self.url

    def get_attribute(self, name):
        return self.attr.get(name, None)

    def get_descendants(self):
        return sum(([node] + node.get_descendants() for node in self.children), [])

    def get_ancestors(self):
        if getattr(self, 'parent', None):
            return [self.parent] + self.parent.get_ancestors()
        else:
            return []

    def is_selected(self, request):
        node_abs_url = self.get_absolute_url()
        return node_abs_url == request.path
