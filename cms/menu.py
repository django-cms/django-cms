from menus.menu_pool import menu_pool
from menus.base import Menu
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
        for page in pages:
            ids.append(page.id)
        titles = list(get_title_queryset(request).filter(page__in=ids, language=lang))
        for page in pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == page.pk:
                    if not hasattr(page, "title_cache"):
                        page.title_cache = {}
                    page.title_cache[title.language] = title
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
                            ids.remove(page.pk)
                            break
                if not ids:
                    break
        return pages
                
menu_pool.register_menu(CMSMenu, "main")