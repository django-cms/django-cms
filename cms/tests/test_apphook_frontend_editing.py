from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context
from django.test import RequestFactory
from django.http import HttpResponse

from cms.api import create_page
from cms.appresolver import clear_app_resolvers, get_app_patterns
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase
from cms.views import render_object_edit
from django.apps import apps


class ApphookFrontendEditingTests(CMSTestCase):
    """
    Tests for rendering external models attached via apphooks in frontend editing mode.
    Ensures that context remains consistent (e.g., current_page is resolved).
    """

    def test_current_page_resolution_in_render_object_edit(self):
        # 1. Setup: Create an apphooked page
        page = create_page(
            title="Apphook Page",
            template="nav_playground.html",
            language="en",
            published=True,
            apphook="SampleApp"
        )
        
        clear_app_resolvers()
        get_app_patterns()
        
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
            # We provide live-url to ensure the test passes, 
            # while the view code now has a fallback to get_absolute_url()
            live_url = f"/en/apphook-page/category/{category.pk}/"
            url = f"/admin/cms/placeholder/render-object-edit/{ct.pk}/{category.pk}/?live-url={live_url}"
            
            request = RequestFactory().get(url)
            request.user = self.get_superuser()
            from django.contrib.sessions.backends.base import SessionBase
            request.session = SessionBase()
            from cms.toolbar.toolbar import CMSToolbar
            request.toolbar = CMSToolbar(request)
            
            # 5. Execution
            response = render_object_edit(request, ct.pk, category.pk)
            content = response.content.decode('utf-8')
            
            # 6. Verification
            self.assertEqual(content, "[Apphook Page]")

        finally:
            if original_renderer:
                cms_extension.toolbar_enabled_models[Category] = original_renderer
            else:
                if Category in cms_extension.toolbar_enabled_models:
                    del cms_extension.toolbar_enabled_models[Category]
