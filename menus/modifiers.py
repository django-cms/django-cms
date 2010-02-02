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
    def modify(self, request, nodes, namespace, root_id, post_cut):
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
        return nodes
                
    def mark_descendants(self, nodes):
        for node in nodes:
            node.descendant = True
            self.mark_descendants(node.children)

menu_pool.register_modifier(Marker)

class Level(Modifier):
    """
    marks all node levels
    """
    post_cut = True
    
    def modify(self, request, nodes, namespace, root_id, post_cut):
        print nodes
        print "============="
        for node in nodes:
            if not node.parent:
                print node
                if post_cut:
                    node.menu_level = 0
                else:
                    node.level = 0
                self.mark_levels(node, post_cut)
            else:
                print node
                print 'parent', node.parent
        return nodes
    
                    
    def mark_levels(self, node, post_cut):
        for child in node.children:
            if post_cut:
                child.menu_level = node.menu_level + 1
            else:
                child.level = node.level + 1
            self.mark_levels(child, post_cut)

menu_pool.register_modifier(Level)

class LoginRequired(Modifier):
    """
    Remove nodes that are login required or require a group
    """
    def modify(self, request, nodes, namespace, root_id, post_cut):
        final = []
        for node in nodes:
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
                final.append(node)
        return final
        
menu_pool.register_modifier(LoginRequired)

        