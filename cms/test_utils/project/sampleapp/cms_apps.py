from cms.app_base import CMSApp
from cms.test_utils.project.sampleapp.cms_menus import SampleAppMenu, StaticMenu3, StaticMenu4
from cms.apphook_pool import apphook_pool
from django.conf.urls import url
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _


class SampleApp(CMSApp):
    name = _("Sample App")
    urls = ["cms.test_utils.project.sampleapp.urls"]
    menus = [SampleAppMenu]
    permissions = True

apphook_pool.register(SampleApp)


class SampleAppWithExcludedPermissions(CMSApp):
    name = _("Sample App with excluded permissions")
    urls = [
        "cms.test_utils.project.sampleapp.urls_excluded"
    ]
    permissions = True
    exclude_permissions = ['excluded']

apphook_pool.register(SampleAppWithExcludedPermissions)


class SampleApp2(CMSApp):
    name = _("Sample App 2")
    urls = ["cms.test_utils.project.sampleapp.urls2"]
    menus = [StaticMenu3]

apphook_pool.register(SampleApp2)


class SampleApp3(CMSApp):
    # CMSApp which returns the url directly rather than trough another Python module
    name = _("Sample App 3")

    def get_urls(self, page=None, language=None, **kwargs):
        def my_view(request):
            return HttpResponse("Sample App 3 Response")

        return [
            url(r'^$', my_view, name='sample3-root'),
        ]

apphook_pool.register(SampleApp3)


class NamespacedApp(CMSApp):
    name = _("Namespaced App")
    urls = [
        "cms.test_utils.project.sampleapp.ns_urls",
        "cms.test_utils.project.sampleapp.urls"
    ]
    menus = [SampleAppMenu, StaticMenu3]
    app_name = 'namespaced_app_ns'

apphook_pool.register(NamespacedApp)


class ParentApp(CMSApp):
    name = _("Parent app")
    urls = ["cms.test_utils.project.sampleapp.urls_parentapp"]

apphook_pool.register(ParentApp)


class ChildApp(CMSApp):
    name = _("Child app")
    urls = ["cms.test_utils.project.sampleapp.urls_childapp"]

apphook_pool.register(ChildApp)


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

apphook_pool.register(VariableUrlsApp)
