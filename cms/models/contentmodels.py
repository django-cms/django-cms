"""Moved to :mod:`cms.pages.models.content`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "ContentAdminManager": "cms.pages.models.content.ContentAdminManager",
        "EmptyPageContent": "cms.pages.models.content.EmptyPageContent",
        "Page": "cms.pages.models.content.Page",
        "PageContent": "cms.pages.models.content.PageContent",
        "PageContentManager": "cms.pages.models.content.PageContentManager",
        "PlaceholderRelationField": "cms.pages.models.content.PlaceholderRelationField",
        "constants": "cms.pages.models.content.constants",
        "get_cms_setting": "cms.pages.models.content.get_cms_setting",
        "models": "cms.pages.models.content.models",
        "provide": "cms.pages.models.content.provide",
        "timezone": "cms.pages.models.content.timezone",
    },
    since="6.0",
    fallback="cms.pages.models.content",
)
