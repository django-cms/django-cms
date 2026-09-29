"""Moved to :mod:`cms.pages.models.page`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "AdminCacheDict": "cms.pages.models.page.AdminCacheDict",
        "Concat": "cms.pages.models.page.Concat",
        "IntegrityError": "cms.pages.models.page.IntegrityError",
        "MP_Node": "cms.pages.models.page.MP_Node",
        "ModelState": "cms.pages.models.page.ModelState",
        "NoReverseMatch": "cms.pages.models.page.NoReverseMatch",
        "Page": "cms.pages.models.page.Page",
        "PageManager": "cms.pages.models.page.PageManager",
        "PageType": "cms.pages.models.page.PageType",
        "PageUrl": "cms.pages.models.page.PageUrl",
        "PageUrlManager": "cms.pages.models.page.PageUrlManager",
        "Prefetch": "cms.pages.models.page.Prefetch",
        "Site": "cms.pages.models.page.Site",
        "UniqueConstraint": "cms.pages.models.page.UniqueConstraint",
        "connection": "cms.pages.models.page.connection",
        "constants": "cms.pages.models.page.constants",
        "force_language": "cms.pages.models.page.force_language",
        "force_str": "cms.pages.models.page.force_str",
        "getLogger": "cms.pages.models.page.getLogger",
        "get_clean_username": "cms.pages.models.page.get_clean_username",
        "get_cms_setting": "cms.pages.models.page.get_cms_setting",
        "get_current_language": "cms.pages.models.page.get_current_language",
        "get_language": "cms.pages.models.page.get_language",
        "get_tree_base": "cms.pages.models.page.get_tree_base",
        "get_user_model": "cms.pages.models.page.get_user_model",
        "i18n": "cms.pages.models.page.i18n",
        "join": "cms.pages.models.page.join",
        "logger": "cms.pages.models.page.logger",
        "model_to_dict": "cms.pages.models.page.model_to_dict",
        "models": "cms.pages.models.page.models",
        "now": "cms.pages.models.page.now",
        "page_caches_invalidated": "cms.pages.models.page.page_caches_invalidated",
        "provide": "cms.pages.models.page.provide",
        "reverse": "cms.pages.models.page.reverse",
        "router": "cms.pages.models.page.router",
        "warnings": "cms.pages.models.page.warnings",
    },
    since="6.0",
    fallback="cms.pages.models.page",
)
