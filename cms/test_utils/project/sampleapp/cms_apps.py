from cms.app_base import CMSApp
from cms.test_utils.project.sampleapp.cms_menus import SampleAppMenu, StaticMenu3
from cms.apphook_pool import apphook_pool
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
