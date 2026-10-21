from django.core.exceptions import ValidationError

from cms.api import create_page
from cms.forms.validators import validate_url_uniqueness
from cms.test_utils.testcases import CMSTestCase


class URLUniquenessTests(CMSTestCase):
    def test_excluding_edited_page_still_checks_its_siblings(self):
        parent = create_page("Parent", "nav_playground.html", "en")
        first = create_page("First", "nav_playground.html", "en", parent=parent)
        second = create_page("Second", "nav_playground.html", "en", parent=parent)

        # The candidate is the edited page's expected parent path plus its new
        # slug. That is not evidence that the path is unique.
        with self.assertRaises(ValidationError):
            validate_url_uniqueness(
                parent.site, first.get_path("en"), "en", exclude_page=second,
            )

    def test_current_page_can_keep_its_own_path(self):
        parent = create_page("Parent", "nav_playground.html", "en")
        child = create_page("Child", "nav_playground.html", "en", parent=parent)

        self.assertTrue(validate_url_uniqueness(
            parent.site, child.get_path("en"), "en", exclude_page=child,
        ))
