from django.utils.crypto import get_random_string

from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.project.sampleapp.models import GrouperModel, ContentModel
from cms.utils.urlutils import admin_reverse


class GrouperChangeListTestCase(CMSTestCase):
    def setUp(self) -> None:
        self.grouper_instance = GrouperModel.objects.create(
            category_name="Grouper Category"
        )
        self.add_url = admin_reverse("sampleapp_groupermodel_add")
        self.change_url = admin_reverse("sampleapp_groupermodel_change", args=(self.grouper_instance.pk,))
        self.changelist_url = admin_reverse("sampleapp_groupermodel_changelist")
        self.admin_user = self.get_superuser()

    def tearDown(self) -> None:
        self.grouper_instance.delete()

    def test_empty_content(self):
        """Without any content being created the changelist shows an empty content text"""
        with self.login_user_context(self.admin_user):
            for language in ("en", "de", "it"):
                response = self.client.get(self.changelist_url + f"?language={language}")
                self.assertContains(response, "Empty content")

    def test_with_content(self):
        """Create one content object and see if it appears in the right admin"""
        random_content = get_random_string(16)
        content = ContentModel.objects.create(
            grouper=self.grouper_instance,
            language="de",
            secret_greeting=random_content,
        )

        with self.login_user_context(self.admin_user):
            response = self.client.get(self.changelist_url + f"?language=de")
            self.assertContains(response, "Grouper Category")
            self.assertContains(response, random_content)

            for language in ("en", "it"):
                response = self.client.get(self.changelist_url + f"?language={language}")
                self.assertContains(response, "Empty content")



