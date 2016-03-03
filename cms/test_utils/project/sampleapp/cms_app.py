from cms.app_base import CMSApp
from cms.test_utils.project.sampleapp.menu import SampleAppMenu
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class SampleApp(CMSApp):
    name = _("Sample App")
    urls = ["cms.test_utils.project.sampleapp.urls"]
    menus = [SampleAppMenu]

apphook_pool.register(SampleApp)


class SampleApp2(CMSApp):
    name = _("Sample App 2")
    urls = ["cms.test_utils.project.sampleapp.urls2"]

apphook_pool.register(SampleApp2)


class NamespacedApp(CMSApp):
    name = _("Namespaced App")
    urls = [
        "cms.test_utils.project.sampleapp.ns_urls",
        "cms.test_utils.project.sampleapp.urls"
    ]
    menus = [SampleAppMenu]
    app_name = 'namespaced_app_ns'

apphook_pool.register(NamespacedApp)
