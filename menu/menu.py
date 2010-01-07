from menu.base import Modifier


class Marker(Modifier):
    
    def modify(self, request, nodes, namespace):
        selected = None
        for node in nodes:
            if node.get_absolute_url() == request.path:
                node.selected = True
                n = node
                while n.parent:
                    n = n.parent
                    n.ancestor = True
            if node.parent.selected:
                node.descendants = True
            if selected and node.parent == selected.parent:
                node.sibling = True
            

class Cutter(Modifier):
    
    def modify(self, request, nodes, namespace):
        for node in nodes:
            