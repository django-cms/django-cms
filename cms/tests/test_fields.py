from cms.api import create_page
from cms.test_utils.project.sampleapp.models import (
    PageOnDeleteCascade,
    PageOnDeleteSetNull,
    PlaceholderOnDeleteCascade,
    PlaceholderOnDeleteSetNull,
)
from cms.test_utils.testcases import CMSTestCase


class PageFieldOnDeleteTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        self.page = create_page(
            'on delete test page',
            template='nav_playground.html',
            language='en',
            published=True,
        )
        self.page.reload()

    def test_page_field_on_delete_cascade(self):
        """
        PageField.on_delete defaults to CASCADE
        """
        on_delete_model = PageOnDeleteCascade.objects.create(page=self.page)
        on_delete_model.page.delete()
        self.assertFalse(PageOnDeleteCascade.objects.filter(pk=on_delete_model.pk).exists())

    def test_page_field_on_delete_set_null(self):
        """
        PageField uses on_delete override
        """
        on_delete_model = PageOnDeleteSetNull.objects.create(page=self.page)
        on_delete_model.page.delete()
        on_delete_model.refresh_from_db()
        self.assertIsNotNone(on_delete_model)
        self.assertIsNone(on_delete_model.page)


class PlaceholderFieldOnDeleteTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        self.page = create_page(
            'on delete test page',
            template='nav_playground.html',
            language='en',
            published=True,
        )
        self.page.reload()
        self.placeholder = self.page.get_placeholders().get(slot='body')

    def test_placeholder_field_on_delete_cascade(self):
        """
        PlaceholderField.on_delete defaults to CASCADE
        """
        on_delete_model = PlaceholderOnDeleteCascade.objects.create(placeholder=self.placeholder)
        on_delete_model.placeholder.delete()
        self.assertFalse(PlaceholderOnDeleteCascade.objects.filter(pk=on_delete_model.pk).exists())

    def test_placeholder_field_on_delete_set_null(self):
        """
        PlaceholderField uses on_delete override
        """
        on_delete_model = PlaceholderOnDeleteSetNull.objects.create(placeholder=self.placeholder)
        on_delete_model.placeholder.delete()
        on_delete_model.refresh_from_db()
        self.assertIsNotNone(on_delete_model)
        self.assertIsNone(on_delete_model.placeholder)
