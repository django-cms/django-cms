from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.urls import re_path, reverse
from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.test_utils.project.sampleapp.cms_menus import SampleAppMenu, StaticMenu3, StaticMenu4

from .models import SampleAppConfig


class AppWithNoMenu(CMSApp):
    app_name = 'app_with_no_menu'

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls"]


class SampleApp(CMSApp):
    name = _("Sample App")
    permissions = True

    def get_menus(self, page=None, language=None, **kwargs):
        return [SampleAppMenu]

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls"]


class SampleAppWithConfig(CMSApp):
    name = _("Sample App with config")
    app_config = SampleAppConfig

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls_sample_config"]

    def get_configs(self):
        return self.app_config.objects.all()

    def get_config(self, namespace):
        try:
            return self.app_config.objects.get(namespace=namespace)
        except ObjectDoesNotExist:
            return None

    def get_config_add_url(self):
        return reverse(f'admin:{self.app_config._meta.app_label}_{self.app_config._meta.model_name}_add')


class SampleAppWithExcludedPermissions(CMSApp):
    name = _("Sample App with excluded permissions")
    permissions = True
    exclude_permissions = ['excluded']

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls_excluded"]


class SampleApp2(CMSApp):
    name = _("Sample App 2")

    def get_menus(self, page=None, language=None, **kwargs):
        return [StaticMenu3]

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls2"]


class SampleApp3(CMSApp):
    # CMSApp which returns the url directly rather than through another Python module
    name = _("Sample App 3")

    def get_urls(self, page=None, language=None, **kwargs):
        def my_view(request):
            return HttpResponse("Sample App 3 Response")

        return [
            re_path(r'^$', my_view, name='sample3-root'),
        ]


class NamespacedApp(CMSApp):
    name = _("Namespaced App")
    app_name = 'namespaced_app_ns'

    def get_menus(self, page=None, language=None, **kwargs):
        return [SampleAppMenu, StaticMenu3]

    def get_urls(self, page=None, language=None, **kwargs):
        return [
            "cms.test_utils.project.sampleapp.ns_urls",
            "cms.test_utils.project.sampleapp.urls"
        ]


class ParentApp(CMSApp):
    name = _("Parent app")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls_parentapp"]


class ChildApp(CMSApp):
    name = _("Child app")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.sampleapp.urls_childapp"]


class VariableUrlsApp(CMSApp):
    name = _("Variable urls-menus App")

    def get_menus(self, page=None, language=None, **kwargs):
        if page and page.reverse_id == 'page1':
            return [SampleAppMenu]
        elif page and page.reverse_id == 'page2':
            return [StaticMenu4]
        else:
            return [StaticMenu4, SampleAppMenu]

    def get_urls(self, page=None, language=None, **kwargs):
        if page and page.reverse_id == 'page1':
            return ["cms.test_utils.project.sampleapp.urls"]

        else:
            return ["cms.test_utils.project.sampleapp.urls2"]


apphook_pool.register(ChildApp)
apphook_pool.register(SampleApp)
apphook_pool.register(SampleAppWithExcludedPermissions)
apphook_pool.register(SampleApp2)
apphook_pool.register(SampleApp3)
apphook_pool.register(NamespacedApp)
apphook_pool.register(ParentApp)
apphook_pool.register(VariableUrlsApp)
