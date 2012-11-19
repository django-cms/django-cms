from cms.models import Page, CMSPlugin
from django.core.management.base import NoArgsCommand


class FixMPTTCommand(NoArgsCommand):
    help = 'Repair MPTT tree for pages'

    def handle_noargs(self, **options):
        """
        Repairs the MPTT tree
        """
        print "fixing mptt page tree"
        Page._tree_manager.rebuild()
        print "fixing mptt plugin tree"
        CMSPlugin.objects.rebuild()
        print "all done"
