from menus.menu_pool import menu_pool
from menus.base import Menu, NavigationNode, Modifier
from cms.utils import get_language_from_request
from cms.utils.moderator import get_page_queryset, get_title_queryset
from django.conf import settings
from django.contrib.sites.models import Site
from cms.utils.i18n import get_fallback_languages

class CMSMenu(Menu):
    
    def get_nodes(self, request):
        page_queryset = get_page_queryset(request)
        site = Site.objects.get_current()
        lang = get_language_from_request(request)
        filters = {
            'in_navigation':True,
            'site':site,
        }
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        pages = page_queryset.published().filter(filters).order_by("tree_id", "lft")
        ids = []
        nodes = []
        for page in pages:
            ids.append(page.id)
        titles = list(get_title_queryset(request).filter(page__in=ids, language=lang))
        for page in pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == page.pk:
                    if not hasattr(page, "title_cache"):
                        page.title_cache = {}
                    page.title_cache[title.language] = title
                    nodes.append(self.page_to_node(page))
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
                            nodes.append(self.page_to_node(page))
                            ids.remove(page.pk)
                            break
                if not ids:
                    break
        return nodes
    
    def page_to_node(self, page):
        attr = {'navigation_extenders':page.navigation_extenders}
        n = NavigationNode(page.get_menu_title(), 
                           page.get_absolute_url(), 
                           page.pk, page.parent_id, 
                           attr=attr,
                           softroot=page.soft_root, 
                           auth_required=page.login_required, 
                           reverse_id=page.reverse_id)
        return n
            
menu_pool.register_menu(CMSMenu)


class NavExtender(Modifier):
    def modify(self, request, nodes, namespace, id, post_cut):
        copy = list(nodes)
        for node in nodes:
            ext = node.attr.get("navigation_extenders", None)
            if ext:
                for n in copy:
                    if n.namespace == ext and not n.parent_id:
                        n.parent_id = node.id
                        n.parent_namespace = node.namespace
                        n.parent = node 
        return nodes
    
menu_pool.register_modifier(NavExtender)