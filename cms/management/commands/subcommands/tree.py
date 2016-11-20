# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from cms.models import Page, CMSPlugin

from .base import SubcommandsCommand


def get_descendant_ids(root_id):
    """
    Returns the a generator of primary keys which represent
    descendants of the given page ID (root_id)
    """
    # Note this is done because get_descendants() can't be trusted
    # as the tree can be corrupt.
    children = Page.objects.filter(parent=root_id).values_list('pk', flat=True)

    for child_id in children.iterator():
        yield child_id

        for descendant_id in get_descendant_ids(child_id):
            yield descendant_id


class FixTreeCommand(SubcommandsCommand):
    help_string = 'Repairing Materialized Path Tree for Pages'
    command_name = 'fix-tree'

    def handle(self, *args, **options):
        """
        Repairs the tree
        """
        self.stdout.write('fixing page tree')
        Page.fix_tree()

        root_draft_pages = Page.objects.filter(
            publisher_is_draft=True,
            parent__isnull=True,
        )

        last = None

        try:
            first = root_draft_pages.order_by('path')[0]
        except IndexError:
            first = None

        for page in root_draft_pages.order_by('site__pk', 'path'):
            if last:
                last = last.reload()
                page = page.reload()
                page.move(target=last, pos='right')
            elif first and first.pk != page.pk:
                page.move(target=first, pos='left')
            last = page.reload()

        root_public_pages = Page.objects.filter(
            publisher_is_draft=False,
            parent__isnull=True,
        ).order_by('publisher_public__path')

        # Filter out any root public pages whose draft page
        # has a parent.
        # This avoids a tree corruption where the public root page
        # is added as a child of the draft page's draft parent
        # instead of the draft page's public parent
        root_public_pages = root_public_pages.filter(
            publisher_public__parent__isnull=True
        )

        for page in root_public_pages:
            page = page.reload()
            public = page.publisher_public
            page.move(target=public, pos='right')

        for root in root_draft_pages.order_by('site__pk', 'path'):
            self._update_descendants_tree(root)

        self.stdout.write('fixing plugin tree')
        CMSPlugin.fix_tree()
        self.stdout.write('all done')

    def _update_descendants_tree(self, root):
        descendants_ids = get_descendant_ids(root.pk)
        public_root_sibling = root.publisher_public

        draft_descendants = (
            Page
            .objects
            .filter(pk__in=descendants_ids)
            .select_related('parent', 'publisher_public')
            .order_by('depth', 'path')
        )

        descendants_by_parent = OrderedDict()

        for descendant in draft_descendants.iterator():
            parent = descendant.parent_id
            descendants_by_parent.setdefault(parent, []).append(descendant)

        for tree in descendants_by_parent.values():
            last_draft = None
            last_public = None
            draft_parent = tree[0].parent
            public_parent = draft_parent.publisher_public

            for draft_page in tree:
                draft_page.refresh_from_db()

                if last_draft:
                    # This is not the loop so this is not the first draft
                    # child. Set this page a sibling of the last processed
                    # draft page.
                    draft_page.move(target=last_draft.reload(), pos='right')
                else:
                    # This is the first time through the loop so this is the first
                    # draft child for this parent.
                    draft_page.move(target=draft_parent.reload(), pos='first-child')

                last_draft = draft_page

                if not draft_page.publisher_public_id:
                    continue

                public_page = draft_page.publisher_public

                if last_public:
                    public_target = last_public
                    public_position = 'right'
                    last_public = public_page
                elif public_parent:
                    # always insert the first public child node found
                    # as the first child of the public parent
                    public_target = public_parent
                    public_position = 'first-child'
                    last_public = public_page
                else:
                    # No public parent has been found
                    # Insert the node as a sibling to the last root sibling
                    # Its very unlikely but possible for the root to not have
                    # a public page. When this happens, use the root draft page
                    # as sibling.
                    public_target = public_root_sibling or root
                    public_position = 'right'
                    # This page now becomes the last root sibling
                    public_root_sibling = public_page

                public_page.refresh_from_db()
                public_page.move(
                    target=public_target.reload(),
                    pos=public_position,
                )
