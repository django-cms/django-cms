from collections import OrderedDict

from cms.models import CMSPlugin, TreeNode

from .base import SubcommandsCommand


def get_descendants(root):
    """
    Returns the a generator of primary keys which represent
    descendants of the given node ID (root_id)
    """
    # Note this is done because get_descendants() can't be trusted
    # as the tree can be corrupt.
    children = TreeNode.objects.filter(parent=root).order_by('path')

    for child in children.iterator():
        yield child

        for descendant in get_descendants(child):
            yield descendant


class FixTreeCommand(SubcommandsCommand):
    help_string = 'Repairing Materialized Path Tree for Pages'
    command_name = 'fix-tree'

    def handle(self, *args, **options):
        """
        Repairs the tree
        """
        self.stdout.write('fixing page tree')
        TreeNode.fix_tree()

        root_nodes = TreeNode.objects.filter(parent__isnull=True)

        last = None

        try:
            first = root_nodes.order_by('path')[0]
        except IndexError:
            first = None

        for node in root_nodes.order_by('site__pk', 'path'):
            if last:
                last.refresh_from_db()
                node.refresh_from_db()
                node.move(target=last, pos='right')
            elif first and first.pk != node.pk:
                node.move(target=first, pos='left')
            last = node

        for root in root_nodes.order_by('site__pk', 'path'):
            self._update_descendants_tree(root)

        self.stdout.write('fixing plugin tree')
        CMSPlugin.fix_tree()
        self.stdout.write('all done')

    def _update_descendants_tree(self, root):
        nodes = TreeNode.objects.all()
        descendants_by_parent = OrderedDict()

        for descendant in get_descendants(root):
            parent_id = descendant.parent_id
            descendants_by_parent.setdefault(parent_id, []).append(descendant)

        for tree in descendants_by_parent.values():
            last_node = None

            for node in tree:
                node.refresh_from_db()

                if last_node:
                    # This is not the first loop so this is not the first draft
                    # child. Set this page a sibling of the last processed
                    # draft page.
                    last_node.refresh_from_db()
                    node.move(target=last_node, pos='right')
                else:
                    # This is the first time through the loop so this is the first
                    # draft child for this parent.
                    node.move(target=nodes.get(pk=tree[0].parent_id), pos='first-child')
                last_node = node
