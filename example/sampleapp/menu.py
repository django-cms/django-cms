from menus.base import Menu, NavigationNode
from example.sampleapp.models import Category
from django.core.urlresolvers import reverse
from menus.menu_pool import menu_pool


class CategoryMenu(Menu):
    def get_nodes(self, request):
        nodes = []
        for cat in Category.objects.all():
            n = NavigationNode(cat.name, cat.get_absolute_url(), "sampleapp", cat.pk, cat.parent_id, "sampleapp")
            nodes.append(n)
        return nodes
    
menu_pool.register_menu(CategoryMenu)


class StaticMenu(Menu):
    def get_nodes(self, request):
        nodes = []
        n = NavigationNode(_('sample root page'), reverse('sample-root'), 1, "static")
        n2 = NavigationNode(_('sample settings page'), reverse('sample-settings'), 2, "static")
        n3 = NavigationNode(_('sample account page'), reverse('sample-account'), 3, "static")
        n4 = NavigationNode(_('sample my profile page'), reverse('sample-profile'), 4, "static", 3, "static")
        nodes.append(n)
        nodes.append(n2)
        nodes.append(n3)
        nodes.append(n4)
        return nodes

menu_pool.register_menu(StaticMenu)
    
class SampleApp(CMSApp):
    name = _("Sample App")
    urls = "sampleapp.urls"
    menus = [CategoryMenu, StaticMenu]
