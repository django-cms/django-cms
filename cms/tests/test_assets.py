import os

from django.test import testcases

import cms


class AssetTestCase(testcases.TestCase):

    def test_css_static_assets_bundled(self):
        version=cms.__version__
        self.assertTrue(os.path.exists(os.path.join("cms", "static", "cms", "css", version)))

    def test_fonts_static_assets_bundled(self):
        version=cms.__version__
        self.assertTrue(os.path.exists(os.path.join("cms", "static", "cms", "fonts", version)))

    def test_js_static_assets_bundled(self):
        version=cms.__version__
        self.assertTrue(os.path.exists(os.path.join("cms", "static", "cms", "js", "dist", version)))
