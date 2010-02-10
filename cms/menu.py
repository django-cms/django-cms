from menus.menu_pool import menu_pool
from menus.base import Menu, NavigationNode, Modifier
from cms.utils import get_language_from_request
from cms.utils.moderator import get_page_queryset, get_title_queryset
from django.conf import settings
from django.contrib.sites.models import Site
from cms.utils.i18n import get_fallback_languages
from cms.exceptions import NoHomeFound

class CMSMenu(Menu):
    
    def get_nodes(self, request):
        page_queryset = get_page_queryset(request)
        site = Site.objects.get_current()
        lang = get_language_from_request(request)
        try:
            home = page_queryset.get_home()
        except NoHomeFound:
            home = None
        filters = {
            'in_navigation':True,
            'site':site,
        }
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        pages = page_queryset.published().filter(filters).order_by("tree_id", "lft")
        ids = []
        nodes = []
        first = True
        home_cut = False
        home_children = []
        for page in pages:
            if home:
                page.home_pk_cache = home.pk
                if first and page.pk != home.pk:
                    home_cut = True
                if (page.parent_id == home.pk or page.parent_id in home_children) and home_cut:
                    page.home_cut_cache = True 
                    home_children.append(page.pk)
            else:
                page.home_pk_cache = -1
            first = False
            ids.append(page.id)
        titles = list(get_title_queryset(request).filter(page__in=ids, language=lang))
        for page in pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == page.pk:
                    if not hasattr(page, "title_cache"):
                        page.title_cache = {}
                    page.title_cache[title.language] = title
                    nodes.append(self.page_to_node(page, home, home_cut))
                    ids.remove(page.pk)
        if ids: # get fallback languages
            fallbacks = get_fallback_languages(lang)
            for l in fallbacks:
                titles = list(get_title_queryset(request).filter(page__in=ids, language=l))
                for title in titles:
                    for page in pages:# add the title and slugs and some meta data
                        if title.page_id == page.pk:
                            if not hasattr(page, "title_cache"):
                                page.title_cache = {}
                            page.title_cache[title.language] = title
                            nodes.append(self.page_to_node(page, home, home_cut))
                            ids.remove(page.pk)
                            break
                if not ids:
                    break
        return nodes
    
    def page_to_node(self, page, home, cut):
        parent_id = page.parent_id
        if home and page.parent_id == home.pk and cut:
            parent_id = None
        attr = {'navigation_extenders':page.navigation_extenders}
        n = NavigationNode(page.get_menu_title(), 
                           page.get_absolute_url(), 
                           page.pk, 
                           parent_id, 
                           attr=attr,
                           softroot=page.soft_root, 
                           auth_required=page.login_required, 
                           reverse_id=page.reverse_id)
        return n
            
menu_pool.register_menu(CMSMenu)


class NavExtender(Modifier):
    def modify(self, request, nodes, namespace, id, post_cut, breadcrumb):
        if post_cut:
            return nodes
        exts = []
        # rearrange the parent relations
        for node in nodes:
            ext = node.attr.get("navigation_extenders", None)
            if ext:
                if not ext in exts:
                    exts.append(ext)
                for n in nodes:
                    if n.namespace == ext and not n.parent_id:
                        n.parent_id = node.id
                        n.parent_namespace = node.namespace
                        n.parent = node
                        node.children.append(n)
        removed = []
        # find all not assigned nodes
        for menu in menu_pool.menus.items():
            if menu[1].cms_enabled and not menu[0] in exts:
                for node in nodes:
                    if node.namespace == menu[0]:
                        removed.append(node)
        if removed:
            # has home a nav extender and is home not in navigation?
            page_queryset = get_page_queryset(request)
            try:
                home = page_queryset.get_home()
            except NoHomeFound:
                home = None  
            if home and not home.in_navigation and home.navigation_extenders:
                n_removed = removed
                removed = []
                for node in n_removed:
                    if node.namespace != home.navigation_extenders:
                        removed.append(node)
        # remove all nodes that are nav_extenders and not assigned 
        for node in removed:
            nodes.remove(node)
        return nodes
    
menu_pool.register_modifier(NavExtender)