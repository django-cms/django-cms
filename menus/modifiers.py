from menus.base import Modifier

class Marker(Modifier):
    """
    searches the current selected node and marks them.
    current_node: selected = True
    siblings: sibling = True
    descendants: descendant = True
    ancestors: ancestor = True
    """
    def modify_all(self, request, nodes, namespace, root_id, post_cut):
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
                else:
                    root_nodes.append(node)
            if node.selected: 
                if node.parent:
                    n = node
                    while n.parent:
                        n = n.parent
                        n.ancestor = True
                    for sibling in node.parent.children:
                        if not sibling.selected:
                            sibling.sibling = True
                else:
                    for n in root_nodes:
                        if not n.selected:
                            n.sibling = True
                if node.children:                    
                    self.mark_descendants(node.children)
                selected = node
            if node.children:
                node.is_leaf_node = False
            else:
                node.is_leaf_node = True
                
    def mark_descendants(self, nodes):
        for node in nodes:
            node.descendant = True
            self.mark_descendants(node.children)


class Level(Modifier):
    """
    marks all node levels
    """
    post_cut = True
    
    def modify(self, request, node, namespace, root_id, post_cut):
        if not node.parent:
            if post_cut:
                node.menu_level = 0
            else:
                node.level = 0
            self.mark_levels(node, post_cut)
    
                    
    def mark_levels(self, node, post_cut):
        for child in node.children:
            if post_cut:
                child.menu_level = node.menu_level + 1
            else:
                child.level = node.level + 1
            self.mark_levels(child, post_cut)


class LoginRequired(Modifier):
    """
    Remove nodes that are login required or require a group
    """
    def modify(self, request, node, namespace, root_id, post_cut):
        good = False
        if node.auth_required and request.user.is_authenticated():
            good = True
        if node.required_group_id and request.user.is_authenticated():
            if not hasattr(request.user, "group_cache"):
                request.user.group_cache = request.user.groups.all()
            good = False
            for group in request.user.group_cache:
                if group.pk == node.required_group_id:
                    good = True
                    break
        if good or (not node.auth_required and not node.required_group_id):
            return node
        self.remove_node(node)
        