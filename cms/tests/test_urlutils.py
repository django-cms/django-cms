from cms.test_utils.testcases import CMSTestCase
from cms.utils import urlutils


class UrlutilsTestCase(CMSTestCase):
    def test_levelize_path(self):
        path = '/application/item/new'
        output = ['/application/item/new', '/application/item', '/application']
        self.assertEqual(urlutils.levelize_path(path), output)

    def test_urljoin(self):
        self.assertEqual('a/b/c/', urlutils.urljoin('a', 'b', 'c'))
        self.assertEqual('a/b/c/', urlutils.urljoin('a', '//b//', 'c'))
        self.assertEqual('a/', urlutils.urljoin('a', ''))

    def test_is_media_url(self):
        with self.settings(MEDIA_URL='/media/'):
            request = self.get_request('/media/')
            self.assertTrue(urlutils.is_media_request(request))
            request = self.get_request('/no-media/')
            self.assertFalse(urlutils.is_media_request(request))
        with self.settings(MEDIA_URL='http://testserver2.com/', ALLOWED_HOSTS=['testserver2.com', 'testserver.com']):
            request = self.get_request('/', domain='testserver.com')
            self.assertFalse(urlutils.is_media_request(request))
        with self.settings(MEDIA_URL='http://testserver.com/media/', ALLOWED_HOSTS=['testserver.com']):
            request = self.get_request('/media/', domain='testserver.com')
            self.assertTrue(urlutils.is_media_request(request))
            request = self.get_request('/no-media/', domain='testserver.com')
            self.assertFalse(urlutils.is_media_request(request))
