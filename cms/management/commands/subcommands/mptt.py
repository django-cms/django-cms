from cms.models import Page, CMSPlugin
from django.core.management.base import NoArgsCommand


class FixMPTTCommand(NoArgsCommand):
    help = 'Repair MPTT tree for pages'

    def handle_noargs(self, **options):
        """
        Repairs the MPTT tree
        """
        self.stdout.write(u"fixing mptt page tree")
        Page._tree_manager.rebuild()
        last = None
        try:
            first = Page.objects.filter(publisher_is_draft=True, parent__isnull=True).order_by('tree_id')[0]
        except IndexError:
            first = None
        for page in Page.objects.filter(publisher_is_draft=True, parent__isnull=True).order_by('site__pk', 'tree_id'):
            if last:
                last = last.reload()
                page = page.reload()
                page.move_to(last, 'right')
            elif first and first.pk != page.pk:
                page.move_to(first, 'left')
            last = page
        for page in Page.objects.filter(publisher_is_draft=False, parent__isnull=True).order_by('publisher_public__tree_id'):
            page = page.reload()
            public = page.publisher_public
            page.move_to(public, 'right')

        self.stdout.write(u"fixing mptt plugin tree")
        CMSPlugin.objects.rebuild()
        self.stdout.write(u"all done")
