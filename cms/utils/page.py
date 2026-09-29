"""Moved to :mod:`cms.pages.utils`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "NoReverseMatch": "cms.pages.utils.NoReverseMatch",
        "PAGE_USERNAME_MAX_LENGTH": "cms.pages.utils.PAGE_USERNAME_MAX_LENGTH",
        "SUFFIX_REGEX": "cms.pages.utils.SUFFIX_REGEX",
        "force_str": "cms.pages.utils.force_str",
        "get_available_slug": "cms.pages.utils.get_available_slug",
        "get_clean_username": "cms.pages.utils.get_clean_username",
        "get_cms_setting": "cms.pages.utils.get_cms_setting",
        "get_current_site": "cms.pages.utils.get_current_site",
        "get_language_from_request": "cms.pages.utils.get_language_from_request",
        "get_page_from_request": "cms.pages.utils.get_page_from_request",
        "get_page_template_from_request": "cms.pages.utils.get_page_template_from_request",
        "re": "cms.pages.utils.re",
        "reverse": "cms.pages.utils.reverse",
    },
    since="6.0",
    fallback="cms.pages.utils",
)
