from unittest.mock import Mock, patch

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404

from cms.api import create_page
from cms.app_registration import get_cms_config_apps, get_cms_extension_apps
from cms.cms_config import CMSCoreExtensions
from cms.models import Page, PageContent
from cms.page_rendering import render_pagecontent
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.setup import setup_cms_apps
from cms.views import render_object_edit, render_object_preview


class ConfigureToolbarEnabledModelsUnitTestCase(CMSTestCase):

    def test_adds_to_mapping(self):
        """Test that a list of (model, render_func) elements gets
        correctly added to internal dict with model as a key
        and render_func as value.
        """
        extensions = CMSCoreExtensions()
        model1 = Mock()
        model2 = Mock()
        render_func1 = Mock()
        render_func2 = Mock()
        config = [(model1, render_func1), (model2, render_func2)]
        cms_config = Mock(
            cms_enabled=True, cms_toolbar_enabled_models=config)
        extensions.configure_toolbar_enabled_models(cms_config)
        self.assertDictEqual(
            extensions.toolbar_enabled_models,
            {model1: render_func1, model2: render_func2},
        )

    def test_doesnt_raise_exception_when_toolbar_enabled_models_undefined(self):
        """
        If the toolbar enabled models setting is not present in the config, simply
        ignore this.
        """
        extensions = CMSCoreExtensions()
        cms_config = Mock(cms_enabled=True, spec=[])
        try:
            extensions.configure_app(cms_config)
        except AttributeError:
            self.fail("Raises exception when cms_toolbar_enabled_models undefined")

    def test_raises_exception_if_not_iterable(self):
        """
        If the toolbar enabled models setting isn't iterable, raise an exception.
        """
        extensions = CMSCoreExtensions()
        cms_config = Mock(
            cms_enabled=True, cms_toolbar_enabled_models=Mock())
        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_toolbar_enabled_models(cms_config)

    @patch('cms.cms_config.logger.warning')
    def test_warning_if_registering_the_same_model_twice(self, mocked_logger):
        """
        If a model is already added to the toolbar enabled models dict,
        log a warning.
        """
        extensions = CMSCoreExtensions()
        model = Mock()
        render_func = Mock()
        config = [(model, render_func), (model, render_func)]
        cms_config = Mock(
            cms_enabled=True, cms_toolbar_enabled_models=config)
        extensions.configure_toolbar_enabled_models(cms_config)
        # Warning message displayed
        mocked_logger.assert_called_once_with(
            f"Model {model} already registered for frontend rendering"
        )
        # Toolbar enabled models dict is still what we expect it to be
        self.assertDictEqual(
            extensions.toolbar_enabled_models,
            {model: render_func},
        )


class ConfigureToolbarEnabledModelsRenderingIntegrationTestCase(CMSTestCase):

    def setUp(self):
        # The results of get_cms_extension_apps and get_cms_config_apps
        # are cached. Clear this cache because installed apps change
        # between tests and therefore unlike in a live environment,
        # results of this function can change between tests
        get_cms_extension_apps.cache_clear()
        get_cms_config_apps.cache_clear()

    def test_adds_all_toolbar_enabled_models_settings_to_dict(self):
        """
        Check that all toolbar enabled models settings are picked up
        from cms.cms_config.
        """
        setup_cms_apps()
        app = apps.get_app_config('cms')
        toolbar_enabled_models = app.cms_extension.toolbar_enabled_models
        self.assertIn(PageContent, toolbar_enabled_models.keys())
        self.assertEqual(toolbar_enabled_models[PageContent], render_pagecontent)


class ToolbarEnabledModelsTestCase(CMSTestCase):

    def test_render_preview_not_supported(self):
        """Test that attempting to use render_object_preview with
        unsupported model returns 400 response.
        """
        request = self.get_request('/')
        request.toolbar = CMSToolbar(request)
        ctype = ContentType.objects.get_for_model(Page)
        page = create_page('home', 'nav_playground.html', 'en')
        response = render_object_preview(request, ctype.pk, page.pk)
        self.assertEqual(response.status_code, 400)

    def test_render_edit_not_supported(self):
        """Test that attempting to use render_object_edit with
        unsupported model returns 400 response.
        """
        request = self.get_request('/')
        request.toolbar = CMSToolbar(request)
        ctype = ContentType.objects.get_for_model(Page)
        page = create_page('home', 'nav_playground.html', 'en')
        response = render_object_edit(request, ctype.pk, page.pk)
        self.assertEqual(response.status_code, 400)

    def test_render_edit_not_editable_model(self):
        """Test that attempting to use render_object_edit with
        a model that doesn't have placeholder field returns 400.
        """
        request = self.get_request('/')
        request.toolbar = CMSToolbar(request)
        ctype = ContentType.objects.get_for_model(Page)
        page = create_page('home', 'nav_playground.html', 'en')
        render_func = Mock()
        mocked_models = {Page: render_func}
        extension = apps.get_app_config('cms').cms_extension
        with patch.object(extension, 'toolbar_enabled_models', mocked_models):
            response = render_object_edit(request, ctype.pk, page.pk)
        # even though Page is registered for toolbar enabled models,
        # it doesn't pass is_editable_model check, so this view returns 400
        self.assertEqual(response.status_code, 400)

    def test_render_preview_object_not_found(self):
        """Test that render_object_object returns 404 when provided
        object id doesn't exist.
        """
        request = self.get_request('/')
        request.toolbar = CMSToolbar(request)
        ctype = ContentType.objects.get_for_model(Page)
        page = create_page('home', 'nav_playground.html', 'en')
        with self.assertRaises(Http404):
            render_object_preview(request, ctype.pk, page.pk + 100)

    def test_render_preview_ctype_not_found(self):
        """Test that render_object_object returns 404 when provided
        content type id doesn't exist.
        """
        request = self.get_request('/')
        request.toolbar = CMSToolbar(request)
        ctype = ContentType.objects.last()
        with self.assertRaises(Http404):
            render_object_preview(request, ctype.pk + 100, 1)

    def test_render_preview_uses_render_func(self):
        """Test that render_object_preview uses render_func associated
        with provided model in CMS config.
        """
        request = self.get_request('/')
        request.toolbar = CMSToolbar(request)
        ctype = ContentType.objects.get_for_model(Page)
        page = create_page('home', 'nav_playground.html', 'en')
        render_func = Mock()
        mocked_models = {Page: render_func}
        extension = apps.get_app_config('cms').cms_extension
        with patch.object(extension, 'toolbar_enabled_models', mocked_models):
            render_object_preview(request, ctype.pk, page.pk)
        render_func.assert_called_once_with(request, page)
