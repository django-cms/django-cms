from cms.apphook_pool import apphook_pool
from cms.app_base import CMSApp
from django.utils.translation import ugettext_lazy as _


class Example1App(CMSApp):
    name = _("Example1 App")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.placeholderapp.urls"]


class MultilingualExample1App(CMSApp):
    name = _("MultilingualExample1 App")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["cms.test_utils.project.placeholderapp.urls_multi"]


apphook_pool.register(Example1App)
apphook_pool.register(MultilingualExample1App)
