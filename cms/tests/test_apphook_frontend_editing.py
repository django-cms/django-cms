import sys

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpResponse
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import clear_url_caches

from cms.api import create_page
from cms.appresolver import clear_app_resolvers
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.toolbar import CMSToolbar
from cms.views import render_object_edit


APP_MODULE = "cms.test_utils.project.sampleapp.cms_apps"


class ApphookFrontendEditingTests(CMSTestCase):
    """
    Tests for rendering external models attached via apphooks in frontend editing mode.
    Ensures that context remains consistent (e.g., current_page is resolved).
    """

    def setUp(self):
        self.apphook_clear()
        self.reload_urls()

    def tearDown(self):
        self.apphook_clear()
        self.reload_urls()

    def reload_urls(self):
        url_modules = [
            'cms.urls',
            APP_MODULE,
            settings.ROOT_URLCONF,
        ]

        clear_app_resolvers()
        clear_url_caches()

        for module in url_modules:
            if module in sys.modules:
                del sys.modules[module]

    def test_current_page_resolution_in_render_object_edit(self):
        # 1. Setup: Create an apphooked page
        superuser = self.get_superuser()
        create_page(
            title="Apphook Page",
            template="nav_playground.html",
            language="en",
            created_by=superuser,
            apphook="SampleApp"
        )
        self.reload_urls()

        # 2. Setup: Create an external model instance (Category)
        category = Category.add_root(name="Test Category")
        ct = ContentType.objects.get_for_model(Category)

        # 3. Setup: Register a mock renderer
        cms_extension = apps.get_app_config('cms').cms_extension

        def mock_render_category(request, obj):
            t = Template("{% load cms_tags %}[{% page_attribute 'page_title' %}]")
            return HttpResponse(t.render(Context({"request": request})))

        original_renderer = cms_extension.toolbar_enabled_models.get(Category)
        cms_extension.toolbar_enabled_models[Category] = mock_render_category

        try:
            # 4. Action: Create a request
            url = f"/admin/cms/placeholder/render-object-edit/{ct.pk}/{category.pk}/"
            request = RequestFactory().get(url)
            request.user = superuser
            request.session = SessionBase()
            request.toolbar = CMSToolbar(request)

            # 5. Execution
            response = render_object_edit(request, ct.pk, category.pk)
            content = response.content.decode('utf-8')

            # 6. Verification
            self.assertEqual(content, "[Apphook Page]")

        finally:
            if original_renderer:
                cms_extension.toolbar_enabled_models[Category] = original_renderer
            elif Category in cms_extension.toolbar_enabled_models:
                del cms_extension.toolbar_enabled_models[Category]
