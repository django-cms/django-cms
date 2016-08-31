# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from cms.models import Page, CMSPlugin

from .base import SubcommandsCommand


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

        self.stdout.write('fixing plugin tree')
        CMSPlugin.fix_tree()
        self.stdout.write('all done')
