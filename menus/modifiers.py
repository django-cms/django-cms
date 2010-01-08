from menus.base import Modifier

class Marker(Modifier):
    """
    searches the current selected node and marks them.
    current_node: selected = True
    siblings: sibling = True
    descendants: descendant = True
    ancestors: ancestor = True
    """
    def modify(self, request, node, root_id):    
        if node.get_absolute_url() == request.path:
            node.selected = True
            n = node
            while n.parent:
                n = n.parent
                n.ancestor = True
            if n.parent:
                for n in n.parent.childrens:
                    if not n.selected:
                        n.sibling = True
            self.mark_descendants(node.childrens)
        return node
            
    def mark_descendants(self, nodes):
        for node in nodes:
            node.descendant = True
            self.mark_descendants(node.childrens)

class LoginRequired(Modifier):
    """
    Remove nodes that are login required or require a group
    """
    def modify(self, request, node, root_id):
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
        if good:
            return node
        return False
        