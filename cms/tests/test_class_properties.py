from cms.admin.forms import AdvancedSettingsForm, ChangePageForm
from cms.models.contentmodels import PageContent
from cms.models.pagemodel import Page
from cms.test_utils.testcases import CMSTestCase


class PagePropsMovedToPageContentTests(CMSTestCase):

    def test_moved_constants(self):
        """test constants moved from Page class"""
        self.assertFalse(hasattr(Page, "LIMIT_VISIBILITY_IN_MENU_CHOICES"))
        self.assertFalse(hasattr(Page, "TEMPLATE_DEFAULT"))
        self.assertFalse(hasattr(Page, "X_FRAME_OPTIONS_INHERIT"))
        self.assertFalse(hasattr(Page, "X_FRAME_OPTIONS_DENY"))
        self.assertFalse(hasattr(Page, "X_FRAME_OPTIONS_SAMEORIGIN"))
        self.assertFalse(hasattr(Page, "X_FRAME_OPTIONS_ALLOW"))
        self.assertFalse(hasattr(Page, "X_FRAME_OPTIONS_CHOICES"))

        """test Page class constants present in PageContent class"""
        self.assertTrue(hasattr(PageContent, "LIMIT_VISIBILITY_IN_MENU_CHOICES"))
        self.assertTrue(hasattr(PageContent, "TEMPLATE_DEFAULT"))
        self.assertTrue(hasattr(PageContent, "X_FRAME_OPTIONS_CHOICES"))

    def test_moved_attributes(self):
        """test xframe_options attribute moved from Page to PageContent"""
        self.assertFalse(hasattr(Page, "xframe_options"))
        self.assertTrue(hasattr(PageContent, "xframe_options"))

        """test xframe_options attribute moved from AdvancedSettingsForm to ChangePageForm"""
        self.assertIsNone(AdvancedSettingsForm.base_fields.get("xframe_options"))
        self.assertIsNotNone(ChangePageForm.base_fields.get("xframe_options"))
