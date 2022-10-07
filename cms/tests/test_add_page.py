import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from cms import api
from cms.models import PagePermission
from cms.test_utils.testcases import CMSTestCase

logger = logging.getLogger(__name__)
User = get_user_model()
language = "en"


class AddPageTestCase(CMSTestCase):

    def add_permission(self, app_label, model, codename):
        content_type = ContentType.objects.get(
            app_label=app_label,
            model=model,
        )
        permission = {
            "codename": codename,
            "content_type": content_type,
        }
        permission = Permission.objects.get(**permission)
        self.group.permissions.add(permission)

    def setUp(self):
        template = settings.CMS_TEMPLATES[0][0]
        site = Site.objects.get(pk=1)
        page = api.create_page("Title", template, language, site=site)
        self.page = page

        group = Group.objects.create(name="editors")
        self.group = group

        user = User.objects.create_user("editor", password="password", email='editor@example.com')
        user.is_staff = True
        user.groups.add(group)
        user.save()
        self.user = user

        self.add_permission("cms", "page", "add_page")
        self.add_permission("cms", "page", "change_page")
        self.add_permission("cms", "page", "delete_page")
        self.add_permission("cms", "page", "publish_page")
        self.add_permission("cms", "page", "view_page")

        PagePermission.objects.create(group=group, page=page)

    def tearDown(self):
        self.group.delete()
        self.user.delete()

    def test_add_page(self):
        self.client.force_login(self.user)

        response = self.client.get('/{}/admin/'.format(language))
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/{}/admin/cms/page/".format(language))
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/{}/admin/cms/page/add/?parent_node={}".format(language, self.page.node.pk))
        self.assertEqual(response.status_code, 200)

        data = {
            "language": language,
            "source": "",
            "title": "test",
            "slug": "test",
            "menu_title": "",
            "page_title": "",
            "meta_description": "",
            "parent_node": self.page.node.pk,
            "_continue": "Save and continue editing"
        }
        response = self.client.post("/{}/admin/cms/page/add/?language={}&parent_node={}".format(language, language, self.page.node.pk), data)
        self.assertEqual(response.status_code, 302)

        location = response.get('Location')
        response = self.client.get(location)
        self.assertEqual(response.status_code, 200)
