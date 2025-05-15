from menus.base import Modifier
from menus.menu_pool import menu_pool


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
