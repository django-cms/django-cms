from cms.app_base import CMSApp
from cms.test.apps.sampleapp.menu import SampleAppMenu
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class SampleApp(CMSApp):
    name = _("Sample App")
    urls = ["cms.test.apps.sampleapp.urls"]
    menus = [SampleAppMenu]
    
apphook_pool.register(SampleApp)
