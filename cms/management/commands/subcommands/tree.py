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
        last = None
        try:
            first = Page.objects.filter(
                publisher_is_draft=True, parent__isnull=True
            ).order_by('path')[0]
        except IndexError:
            first = None
        for page in Page.objects.filter(
            publisher_is_draft=True, parent__isnull=True
        ).order_by('site__pk', 'path'):
            if last:
                last = last.reload()
                page = page.reload()
                page.move(target=last, pos='right')
            elif first and first.pk != page.pk:
                page.move(target=first, pos='left')
            last = page.reload()
        for page in Page.objects.filter(
            publisher_is_draft=False, parent__isnull=True
        ).order_by('publisher_public__path'):
            page = page.reload()
            public = page.publisher_public
            page.move(target=public, pos='right')

        self.stdout.write('fixing plugin tree')
        CMSPlugin.fix_tree()
        self.stdout.write('all done')
