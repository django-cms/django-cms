from __future__ import with_statement
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.api import create_page
from django.contrib.auth.models import User

class ToolbarTests(SettingsOverrideTestCase):
    settings_overrides = {'CMS_MODERATOR': False}
    
    def setUp(self):
        superuser = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = create_page("apphooked-page", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        self.assertTrue(page.publish())
        
    def test_apphook_on_root(self):
        response = self.client.get('/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'nav_playground.html')
        self.assertContains(response, '<div id="cms_toolbar"')
        self.assertContains(response, 'cms.placeholders.js')
        self.assertContains(response, 'cms.placeholders.css')