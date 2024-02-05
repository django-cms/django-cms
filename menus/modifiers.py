from menus.base import Modifier
from menus.menu_pool import menu_pool


class Marker(Modifier):
    """
    Searches the current selected node and marks them.
    - current_node (bool): Whether the current node is selected.
    - siblings (bool): Whether siblings of the current node are marked.
    - descendants (bool): Whether descendants of the current node are marked.
    - ancestors (bool): Whether ancestors of the current node are marked.
    """
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
        Modify the given list of nodes based on the specified conditions.

        Args:
            self: The current instance of the class.
            request: The request object associated with the operation.
            nodes (list): A list of node objects.
            namespace: The namespace associated with the nodes.
            root_id: The ID of the root node.
            post_cut (bool): Flag indicating whether the modification is being done after the cut operation.
            breadcrumb (bool): Flag indicating whether the breadcrumb data is being used.

        Returns:
            list: The modified list of nodes.
        """
        """"""
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

        Args:
            node (Node): The root node of the menu hierarchy.
            post_cut (bool): Flag indicating whether the function is called after a cut is made.

        Returns:
            None

        Raises:
            None
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

        Args:
            self: The instance of the class containing this method.
            request: The current request object.
            nodes (list): A list of nodes to be modified.
            namespace: The namespace.
            root_id: The ID of the root node.
            post_cut (bool): Flag indicating if the modification is happening after cutting.
            breadcrumb (bool): Flag indicating if the modification is happening for the breadcrumb.

        Returns:
            list: The modified list of nodes.
        """
        """"""
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
    Register the Marker, AuthVisibility, and Level modifiers to the menu pool.
    """
    menu_pool.register_modifier(Marker)
    menu_pool.register_modifier(AuthVisibility)
    menu_pool.register_modifier(Level)
