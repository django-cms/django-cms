"""Moved to :mod:`cms.pages.rendering`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "EmptyPageContent": "cms.pages.rendering.EmptyPageContent",
        "Http404": "cms.pages.rendering.Http404",
        "HttpResponseRedirect": "cms.pages.rendering.HttpResponseRedirect",
        "Resolver404": "cms.pages.rendering.Resolver404",
        "TemplateResponse": "cms.pages.rendering.TemplateResponse",
        "admin_reverse": "cms.pages.rendering.admin_reverse",
        "constants": "cms.pages.rendering.constants",
        "render_page": "cms.pages.rendering.render_page",
        "render_pagecontent": "cms.pages.rendering.render_pagecontent",
        "resolve": "cms.pages.rendering.resolve",
        "reverse": "cms.pages.rendering.reverse",
        "set_page_cache": "cms.pages.rendering.set_page_cache",
        "settings": "cms.pages.rendering.settings",
        "user_can_change_page": "cms.pages.rendering.user_can_change_page",
        "user_can_view_page": "cms.pages.rendering.user_can_view_page",
    },
    since="6.0",
    fallback="cms.pages.rendering",
)
