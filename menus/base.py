from typing import Any, Dict, List, Optional

from django.utils.encoding import smart_str


class Menu:
    """The base class for all menu-generating classes."""
    namespace = None

    def __init__(self, renderer):
        """
        Initialize the Menu class.

        Args:
            renderer: The renderer associated with the menu.
        """
        self.renderer = renderer

        if not self.namespace:
            self.namespace = self.__class__.__name__

    def get_nodes(self, request) -> List['NavigationNode']:
        """
        Get a list of NavigationNode instances for the menu.

        Args:
            request: The request object.

        Returns:
            A list of NavigationNode instances.
        """
        raise NotImplementedError


class Modifier:
    """The base class for all menu-modifying classes. A modifier add, removes or changes
    :class:`menus.base.NavigationNode` in the list."""
    def __init__(self, renderer):
        """
        Initialize the Modifier class.

        Args:
            renderer: The renderer associated with the modifier.
        """
        self.renderer = renderer

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        """
        Modify the list of nodes.

        Args:
            request: The request object.
            nodes: List of NavigationNode instances.
            namespace: The namespace for the menu.
            root_id: ID of the root node.
            post_cut: Boolean indicating post-cut status.
            breadcrumb: Boolean indicating breadcrumb status.
        """
        pass


class NavigationNode:
    """
    Represents each node in a menu tree.

    Attributes:
        title: The title of the menu item.
        url: The URL associated with the menu item.
        id: The unique ID of this item.
        parent_id: The ID of the parent item (optional).
        parent_namespace: The namespace of the parent (optional).
        attr: Additional information to store on this node (optional).
        visible: Indicates whether this item is visible (default is True).
    """

    selected: bool = False
    sibling: bool = False
    ancestor: bool = False
    descendant: bool = False

    def __init__(
        self,
        title: str,
        url: str,
        id: Any,
        parent_id: Optional[Any] = None,
        parent_namespace: Optional[str] = None,
        attr: Optional[Dict[str, Any]] = None,
        visible: bool = True,
    ):
        """
        Initialize a NavigationNode instance.

        Args:
            title: The title of the menu item.
            url: The URL associated with the menu item.
            id: The unique ID of this item.
            parent_id: The ID of the parent item (optional).
            parent_namespace: The namespace of the parent (optional).
            attr: Additional information to store on this node (optional).
            visible: Indicates whether this item is visible (default is True).
        """
        self.children: List[NavigationNode] = []  # Do not modify
        self.parent: Optional[NavigationNode] = None  # Do not modify, code depends on this
        self.namespace: Optional[str] = None  # TODO: Clarify the necessity of this and the line above
        self.title = title
        self.url = url
        self.id = id
        self.parent_id = parent_id
        self.parent_namespace = parent_namespace
        self.visible = visible
        self.attr = attr or {}
        """
        A dictionary to add arbitrary attributes to the node. An important key is 'is_page':
        * If True, the node represents a django CMS 'Page' object.
        * Nodes representing CMS pages have specific keys in 'attr'.
        """

    def __repr__(self):
        """
        Returns a string representation of the NavigationNode.
        """
        return f"<Navigation Node: {smart_str(self.title)}>"

    def get_menu_title(self) -> str:
        """
        Returns the associated title using the naming convention of 'cms.models.pagemodel.Page'.
        """
        return self.title

    def get_absolute_url(self) -> str:
        """
        Returns the URL associated with this menu item.
        """
        return self.url

    def get_attribute(self, name: str) -> Any:
        """
        Retrieves a dictionary item from 'attr'. Returns None if it does not exist.

        Args:
            name: The name of the attribute.

        Returns:
            The value associated with the attribute name or None if not found.
        """
        return self.attr.get(name, None)

    def get_descendants(self) -> List['NavigationNode']:
        """
        Returns a list of all children beneath the current menu item.
        """
        return sum(([node] + node.get_descendants() for node in self.children), [])

    def get_ancestors(self) -> List['NavigationNode']:
        """
        Returns a list of all parent items, excluding the current menu item.
        """
        if getattr(self, 'parent', None):
            return [self.parent] + self.parent.get_ancestors()
        else:
            return []

    def is_selected(self, request) -> bool:
        """
        Checks if the node is selected based on the request path.

        Args:
            request: The request object.

        Returns:
            True if the node is selected, False otherwise.
        """
        node_abs_url = self.get_absolute_url()
        return node_abs_url == request.path
