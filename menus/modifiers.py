from menus.base import Modifier
from menus.menu_pool import menu_pool


class Marker(Modifier):
    """
    searches the current selected node and marks them.
    current_node: selected = True
    siblings: sibling = True
    descendants: descendant = True
    ancestors: ancestor = True
    """
    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
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
        for node in nodes:
            node.descendant = True
            self.mark_descendants(node.children)


class Level(Modifier):
    """
    marks all node levels
    """
    post_cut = True

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
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
        if post_cut or breadcrumb:
            return nodes
        final = []
        for node in nodes:
            if (node.attr.get('visible_for_authenticated', True) and request.user.is_authenticated) or \
                    (node.attr.get('visible_for_anonymous', True) and not request.user.is_authenticated):
                final.append(node)
            else:
                if node.parent and node in node.parent.children:
                    node.parent.children.remove(node)
        return final


def register():
    menu_pool.register_modifier(Marker)
    menu_pool.register_modifier(AuthVisibility)
    menu_pool.register_modifier(Level)
