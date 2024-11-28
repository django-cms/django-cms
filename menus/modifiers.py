from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
from menus.base import Modifier
from menus.menu_pool import menu_pool


class Marker(Modifier):
    """
    Searches the current selected node and marks them.

    :param current_node: Whether the current node is selected.
    :type current_node: bool
    :param sibling: Whether siblings of the current node are marked.
    :type sibling: bool
    :param descendant: Whether descendants of the current node are marked.
    :type descendant: bool
    :param ancestor: Whether ancestors of the current node are marked.
    :type ancestor: bool

    .. note::

       This modifier is deprecated and will be removed in django CMS 4.3. The menu pool now provides the same
       functionality out of the box.
    """

    def __init__(self, *args, **kwargs):
        import warnings

        warnings.warn(
            "The Marker modifier is deprecated and will be removed. The functionality is now provided "
            "by the menu_pool itself.",
            RemovedInDjangoCMS43Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        """
        Modifies a list of nodes based on certain conditions.

        Args:
            self: The current object of the class.
            request: The request object.
            nodes (list): A list of node objects.
            namespace: The namespace of the nodes.
            root_id: The root ID of the nodes.
            post_cut (bool): A flag indicating whether post_cut condition is met.
            breadcrumb (bool): A flag indicating whether breadcrumb condition is met.

        Returns:
            list: The modified list of nodes based on the conditions.
        """
        """"""
        if post_cut or breadcrumb:
            return nodes
        selected = None
        root_nodes = []
        for node in nodes:
            if not hasattr(node, "descendant"):
                node.descendant = False
            if not hasattr(node, "ancestor"):
                node.ancestor = False
            if not node.parent:
                if selected and not selected.parent:
                    node.sibling = True
                root_nodes.append(node)
            if node.selected:
                if node.parent:
                    newnode = node
                    while newnode.parent:
                        newnode = newnode.parent
                        newnode.ancestor = True
                    for sibling in node.parent.children:
                        if not sibling.selected:
                            sibling.sibling = True
                else:
                    for root_node in root_nodes:
                        if not root_node.selected:
                            root_node.sibling = True
                if node.children:
                    self.mark_descendants(node.children)
                selected = node
            if node.children:
                node.is_leaf_node = False
            else:
                node.is_leaf_node = True
        return nodes

    def mark_descendants(self, nodes):
        """
        Mark the descendants of the given nodes.

        Args:
            nodes (list): A list of nodes to mark their descendants.

        Returns:
            None

        Raises:
            None
        """
        for node in nodes:
            node.descendant = True
            self.mark_descendants(node.children)


class Level(Modifier):
    """
    Marks all node levels.
    """
    post_cut = True

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        """
        Modify the list of nodes based on certain conditions.

        :param self: The instance of the class containing this method.
        :param request: The current request object.
        :param nodes: A list of nodes to be modified.
        :type nodes: list
        :param namespace: The namespace.
        :param root_id: The ID of the root node.
        :param post_cut: Flag indicating if the modification is happening after cutting.
        :type post_cut: bool
        :param breadcrumb: Flag indicating if the modification is happening for the breadcrumb.
        :type breadcrumb: bool
        :return: The modified list of nodes.
        :rtype: list
        """

        if breadcrumb:
            return nodes
        for node in nodes:

            if not node.parent:
                if post_cut:
                    node.menu_level = 0
                else:
                    node.level = 0
                self.mark_levels(node, post_cut)

        return nodes

    def mark_levels(self, node, post_cut):
        """
        Mark the levels of menu items.

        :param node: The root node of the menu hierarchy.
        :type node: Node
        :param post_cut: Flag indicating whether the function is called after a cut is made.
        :type post_cut: bool
        :returns: None
        :rtype: None
        :raises None: This function does not raise any exceptions.
        """
        for child in node.children:
            if post_cut:
                child.menu_level = node.menu_level + 1
            else:
                child.level = node.level + 1
            self.mark_levels(child, post_cut)


class AuthVisibility(Modifier):
    """
    Remove nodes that are login required or require a group
    """
    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        """
        Modify the list of nodes based on certain conditions.

        :param self: The instance of the class containing this method.
        :param request: The current request object.
        :param nodes: A list of nodes to be modified.
        :type nodes: list
        :param namespace: The namespace.
        :param root_id: The ID of the root node.
        :param post_cut: Flag indicating if the modification is happening after cutting.
        :type post_cut: bool
        :param breadcrumb: Flag indicating if the modification is happening for the breadcrumb.
        :type breadcrumb: bool
        :return: The modified list of nodes.
        :rtype: list
        """
        if post_cut or breadcrumb:
            return nodes
        final = []
        for node in nodes:
            if (node.attr.get('visible_for_authenticated', True) and request.user.is_authenticated) or \
                    (node.attr.get('visible_for_anonymous', True) and not request.user.is_authenticated):
                final.append(node)
            elif node.parent and node in node.parent.children:
                node.parent.children.remove(node)
        return final


def register():
    """
    Register the AuthVisibility and Level modifiers to the menu pool.
    """
    menu_pool.register_modifier(AuthVisibility)
    menu_pool.register_modifier(Level)
