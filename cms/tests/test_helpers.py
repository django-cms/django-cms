from cms.models import Page, PageContent
from cms.test_utils.project.sampleapp.models import (
    Category,
    Picture,
    SomeEditableModel,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils.helpers import is_editable_model


class HelperTests(CMSTestCase):

    def test_is_editable_model(self):
        # Model has registered through cms_config.
        # Returns True.
        self.assertTrue(is_editable_model(PageContent))

        # Model has placeholder relationship but is not registered through cms_config.
        # Returns False.
        self.assertFalse(is_editable_model(Category))

        # Model has no placeholder relationship and no admin class.
        # Returns False.
        self.assertFalse(is_editable_model(Picture))

        # Model has no placeholder relationship
        # but has admin class which inherits from FrontendEditableAdminMixin AND has get_absolute_url.
        # Returns True.
        self.assertTrue(is_editable_model(SomeEditableModel))

        # Model has no placeholder relationship.
        # but has admin class which is not inherited from FrontendEditableAdminMixin.
        # Returns False.
        self.assertFalse(is_editable_model(Page))
