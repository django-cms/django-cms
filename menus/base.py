from django.utils.encoding import smart_str


class Menu(object):
    """The base class for all menu-generating classes."""
    namespace = None

    def __init__(self, renderer):
        self.renderer = renderer

        if not self.namespace:
            self.namespace = self.__class__.__name__

    def get_nodes(self, request):
        """Each subclass of Menu should return a list of :class:`menus.base.NavigationNode` instances."""
        raise NotImplementedError


class Modifier(object):
    """The base class for all menu-modifying classes. A modifier add, removes or changes
    :class:`menus.base.NavigationNode` in the list."""
    def __init__(self, renderer):
        self.renderer = renderer

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        """Each subclass of :class:`Modifier` should implement a :meth:`modify` method."""
        pass


class NavigationNode(object):
    """
    Each node in a menu tree is represented by a ``NavigationNode`` instance.
    """
    selected = None
    sibling = False
    ancestor = False
    descendant = False

    def __init__(self, title, url, id, parent_id=None, parent_namespace=None,
                 attr=None, visible=True):
        """
        :param str title: The title to display this menu item with.
        :param str url: The URL associated with this menu item.
        :param id: Unique (for the current tree) ID of this item.
        :param parent_id: Optional, ID of the parent item.
        :param parent_namespace: Optional, namespace of the parent.
        :param dict attr: Optional, dictionary of additional information to store on
                          this node.
        :param bool visible: Optional, defaults to ``True``, whether this item is
                             visible or not.
        """
        self.children = []  # do not touch
        self.parent = None  # do not touch, code depends on this
        self.namespace = None  # TODO: Assert why we need this and above
        self.title = title
        self.url = url
        self.id = id
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        self.visible = visible
        self.attr = attr or {}  # To avoid declaring a dict in defaults...
        """
        A dictionary, provided in order that arbitrary attributes may be added to the node -
        placing them directly on the node itself could cause a clash with an existing or future attribute.

        An important key in this dictionary is ``is_page``: if ``True``, the node represents a django CMS
        ``Page`` object.

        Nodes that represent CMS pages have the following keys in ``attr``:

        * **auth_required** (*bool*) – is authentication required to access this page
        * **is_page** (*bool*) – Always True
        * **navigation_extenders** (*list*) – navigation extenders connected to this node
        * **redirect_url** (*str*) – redirect URL of page (if any)
        * **reverse_id** (*str*) – unique identifier for the page
        * **soft_root** (*bool*) – whether page is a soft root
        * **visible_for_authenticated** (*bool*) – visible for authenticated users
        * **visible_for_anonymous** (*bool*) – visible for anonymous users
        """

    def __repr__(self):
        return "<Navigation Node: %s>" % smart_str(self.title)

    def get_menu_title(self):
        """Utility method to return the associated title, using the same naming
        convention used by :class:`cms.models.pagemodel.Page`."""
        return self.title

    def get_absolute_url(self):
        """Utility method to return the URL associated with this menu item,
        primarily to follow naming convention asserted by Django."""
        return self.url

    def get_attribute(self, name):
        """Retrieves a dictionary item from :attr:`attr`. Returns ``None``  if it does not exist."""
        return self.attr.get(name, None)

    def get_descendants(self):
        """Returns a list of all children beneath the current menu item."""
        return sum(([node] + node.get_descendants() for node in self.children), [])

    def get_ancestors(self):
        """Returns a list of all parent items, excluding the current menu item."""
        if getattr(self, 'parent', None):
            return [self.parent] + self.parent.get_ancestors()
        else:
            return []

    def is_selected(self, request):
        node_abs_url = self.get_absolute_url()
        return node_abs_url == request.path
