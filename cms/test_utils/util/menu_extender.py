# -*- coding: utf-8 -*-

from menus.base import NavigationNode
from menus.menu_pool import menu_pool
from cms.menu_bases import CMSAttachMenu


class TestMenu(CMSAttachMenu):
    name = "test menu"

    def get_nodes(self, request):
        nodes = []
        n = NavigationNode('sample root page', "/", 1)
        n2 = NavigationNode('sample settings page', "/bye/", 2)
        n3 = NavigationNode('sample account page', "/hello/", 3)
        n4 = NavigationNode('sample my profile page', "/hello/world/", 4, 3)
        nodes.append(n)
        nodes.append(n2)
        nodes.append(n3)
        nodes.append(n4)
        return nodes

menu_pool.register_menu(TestMenu)
