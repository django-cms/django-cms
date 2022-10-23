import codecs
import tempfile

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from django.core.management import call_command

from cms.models import CMSPlugin, Page, Placeholder, TreeNode
from cms.test_utils.fixtures.navextenders import NavextendersFixture
from cms.test_utils.testcases import CMSTestCase


class FixtureTestCase(NavextendersFixture, CMSTestCase):

    def test_fixture_load(self):
        """
        This test dumps a live set of pages, cleanup the database and load it
        again.
        This makes fixtures unnecessary and it's easier to maintain.
        """
        output = StringIO()
        dump = tempfile.mkstemp(".json")
        call_command('dumpdata', 'cms', indent=3, stdout=output)
        original_ph = Placeholder.objects.count()
        original_pages = Page.objects.count()
        original_tree_nodes = TreeNode.objects.count()
        original_plugins = CMSPlugin.objects.count()
        Page.objects.all().delete()
        Placeholder.objects.all().delete()
        TreeNode.objects.all().delete()
        output.seek(0)
        with codecs.open(dump[1], 'w', 'utf-8') as dumpfile:
            dumpfile.write(output.read())

        self.assertEqual(0, TreeNode.objects.count())
        self.assertEqual(0, Page.objects.count())
        self.assertEqual(0, Placeholder.objects.count())
        # Transaction disable, otherwise the connection it the test would be
        # isolated from the data loaded in the different command connection
        call_command('loaddata', dump[1], stdout=output)
        self.assertEqual(5, Page.objects.count())
        self.assertEqual(original_pages, Page.objects.count())
        self.assertEqual(5, TreeNode.objects.count())
        self.assertEqual(original_tree_nodes, TreeNode.objects.count())
        # Placeholder number may differ if signals does not correctly handle
        # load data command
        self.assertEqual(original_ph, Placeholder.objects.count())
        self.assertEqual(original_plugins, CMSPlugin.objects.count())
