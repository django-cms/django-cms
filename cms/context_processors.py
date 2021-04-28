from functools import lru_cache

from django.utils.functional import lazy

from cms.utils.conf import get_cms_setting
from cms.utils.page import get_page_template_from_request


def cms_settings(request):
    """
    Adds cms-related variables to the context.
    """
    from menus.menu_pool import MenuRenderer

    @lru_cache(maxsize=None)
    def _get_menu_renderer():
        # We use lru_cache to avoid getting the manager
        # every time this function is called.
        from menus.menu_pool import menu_pool
        return menu_pool.get_renderer(request)

    # Now use lazy() to avoid getting the menu renderer
    # up until the point is needed.
    # lazy() does not memoize results, is why lru_cache is needed.
    _get_menu_renderer = lazy(_get_menu_renderer, MenuRenderer)

    return {
        'cms_menu_renderer': _get_menu_renderer(),
        'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        'CMS_TEMPLATE': lambda: get_page_template_from_request(request),
    }
