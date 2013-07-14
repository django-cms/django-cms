from cms.test_utils.testcases import CMSTestCase

from cms.extensions import *


class ExtensionsTestCase(CMSTestCase):
    def test_register_extension(self):
        self.assertIs(extension_pool.signaling_activated, False)

        # --- None extension registering -----------------------------
        from cms.exceptions import SubClassNeededError
        none_extension = self.get_none_extension_class()
        self.assertRaises(SubClassNeededError, extension_pool.register, none_extension)
        self.assertEqual(len(extension_pool.page_extensions), 0)
        self.assertEqual(len(extension_pool.title_extensions), 0)
        self.assertIs(extension_pool.signaling_activated, False)

        # --- Page registering ---------------------------------------
        page_extension = self.get_page_extension_class()

        # register first time
        extension_pool.register(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), 1)

        # register second time
        extension_pool.register(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), 1)

        self.assertIs(extension_pool.signaling_activated, True)

        # --- Title registering --------------------------------------
        title_extension = self.get_title_extension_class()

        # register first time
        extension_pool.register(title_extension)
        self.assertEqual(len(extension_pool.title_extensions), 1)

        # register second time
        extension_pool.register(title_extension)
        self.assertEqual(len(extension_pool.title_extensions), 1)

        self.assertIs(extension_pool.signaling_activated, True)

        # --- Unregister ---------------------------------------------
        extension_pool.unregister(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), 0)

        extension_pool.register(title_extension)
        self.assertEqual(len(extension_pool.title_extensions), 0)

    def get_page_extension_class(self):
        from django.db import models

        class TestPageExtension(PageExtension):
            content = models.CharField('Content', max_length=50)

        return TestPageExtension

    def get_title_extension_class(self):
        from django.db import models

        class TestTitleExtension(TitleExtension):
            content = models.CharField('Content', max_length=50)

        return TestTitleExtension

    def get_none_extension_class(self):
        class TestNoneExtension(object):
            pass

        return TestNoneExtension
