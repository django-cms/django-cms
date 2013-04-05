from cms.models import Page, CMSPlugin
from django.core.management.base import NoArgsCommand


class FixMPTTCommand(NoArgsCommand):
    help = 'Repair MPTT tree for pages'

    def handle_noargs(self, **options):
        """
        Repairs the MPTT tree
        """
        self.stdout.write("fixing mptt page tree")
        Page._tree_manager.rebuild()
        self.stdout.write("fixing mptt plugin tree")
        CMSPlugin.objects.rebuild()
        self.stdout.write("all done")
