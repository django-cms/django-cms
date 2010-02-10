from cms.app_base import CMSApp
from example.sampleapp.menu import SampleAppMenu
from cms.apphook_pool import apphook_pool

class SampleApp(CMSApp):
    name = _("Sample App")
    urls = ["sampleapp.urls"]
    menus = [SampleAppMenu]
    
apphook_pool.register(SampleApp)