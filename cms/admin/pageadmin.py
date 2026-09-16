"""Moved to :mod:`cms.pages.admin.page`.

Kept importable because third-party packages subclass these by this path
(see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "PAGE_SMART_LINK_MAX_RESULTS": "cms.pages.admin.page.PAGE_SMART_LINK_MAX_RESULTS",
        "PageAdmin": "cms.pages.admin.page.PageAdmin",
        "PageContentAdmin": "cms.pages.admin.page.PageContentAdmin",
        "PageDeleteMessageMixin": "cms.pages.admin.page.PageDeleteMessageMixin",
    },
    since="6.0",
    fallback="cms.pages.admin.page",
)
