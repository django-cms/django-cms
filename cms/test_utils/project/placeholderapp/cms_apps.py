from cms.apphook_pool import apphook_pool
from cms.app_base import CMSApp
from django.utils.translation import ugettext_lazy as _


class Example1App(CMSApp):
    name = _("Example1 App")
    urls = ["cms.test_utils.project.placeholderapp.urls"]

apphook_pool.register(Example1App)


class MultilingualExample1App(CMSApp):
    name = _("MultilingualExample1 App")
    urls = ["cms.test_utils.project.placeholderapp.urls_multi"]

apphook_pool.register(MultilingualExample1App)
