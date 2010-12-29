from cms.tests.base import CMSTestCase
from cms.utils import urlutils


class UrlutilsTestCase(CMSTestCase):
    def test_01_levelize_path(self):
        path = '/application/item/new'
        output = ['/application/item/new', '/application/item', '/application']
        self.assertEqual(urlutils.levelize_path(path), output)
        
    def test_02_urljoin(self):
        self.assertEqual('a/b/c/', urlutils.urljoin('a', 'b', 'c'))
        self.assertEqual('a/b/c/', urlutils.urljoin('a', '//b//', 'c'))
        self.assertEqual('a/', urlutils.urljoin('a', ''))