from django.contrib.admin.utils import flatten_fieldsets

from cms.admin.forms import ChangePageForm
from cms.models.contentmodels import PageContent
from cms.test_utils.testcases import CMSTestCase


class PagePropsMovedToPageContentTests(CMSTestCase):

    def test_moved_fields(self):
        non_editables = [
            'id',
            'changed_by',
            'changed_date',
            'created_by',
            'creation_date',
            'page_id',
            'in_navigation',
            'language'
        ]

        change_page_form_fieldsets = flatten_fieldsets(ChangePageForm.fieldsets)
        page_content_fields = [field.attname for field in PageContent._meta.fields]

        # filter the non editables from PageContent fields
        filtered_page_content_fields = list(set(page_content_fields) - set(non_editables))

        for field in filtered_page_content_fields:
            self.assertIn(field, change_page_form_fieldsets)
