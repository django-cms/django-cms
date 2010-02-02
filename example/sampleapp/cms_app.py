from cms.app_base import CMSApp
from example.sampleapp.menu import StaticMenu, CategoryMenu
from cms.apphook_pool import apphook_pool

class SampleApp(CMSApp):
    name = _("Sample App")
    urls = "sampleapp.urls"
    menus = [CategoryMenu, StaticMenu]
    
apphook_pool.register(SampleApp)