"""Cross-container cache invalidation.

The model layer announces what it invalidated (:mod:`cms.shared.signals`); the
reactions that reach into *another* container live here, where importing that
container is safe. ``cms.signals`` is imported last by ``cms.models``, so these
handlers may import freely without reintroducing the cycles they replace.
"""

from cms.utils.conf import get_cms_setting


def invalidate_page_cache_for_placeholder(sender, **kwargs):
    """Clearing a placeholder's cache makes every cached page stale.

    Cached pages embed rendered placeholder content, so the CMS drops the whole
    page cache rather than tracking which pages a placeholder appears on. This
    ran inside ``Placeholder.clear_cache`` until the core container stopped
    importing the page cache.
    """
    if get_cms_setting("PAGE_CACHE"):
        from cms.cache import invalidate_cms_page_cache

        invalidate_cms_page_cache()


def clear_menu_cache_for_page(sender, menu=False, page=None, **kwargs):
    """Drop the navigation cache for a page's site after a structural change.

    Only when the caller asked for it: a plain content edit does not change
    navigation, but a move, delete or slug change does. This ran inside
    ``Page.clear_cache`` until the pages container stopped importing
    ``menus.menu_pool`` from its model layer.
    """
    if not menu:
        return

    from menus.menu_pool import menu_pool

    menu_pool.clear(site_id=page.site_id if page else None)
