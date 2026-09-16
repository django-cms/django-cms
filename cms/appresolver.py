"""Moved to :mod:`cms.pages.appresolver`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "APP_RESOLVERS": "cms.pages.appresolver.APP_RESOLVERS",
        "AppRegexURLResolver": "cms.pages.appresolver.AppRegexURLResolver",
        "ImproperlyConfigured": "cms.pages.appresolver.ImproperlyConfigured",
        "NoReverseMatch": "cms.pages.appresolver.NoReverseMatch",
        "OperationalError": "cms.pages.appresolver.OperationalError",
        "OrderedDict": "cms.pages.appresolver.OrderedDict",
        "Page": "cms.pages.appresolver.Page",
        "ProgrammingError": "cms.pages.appresolver.ProgrammingError",
        "RegexPattern": "cms.pages.appresolver.RegexPattern",
        "Resolver404": "cms.pages.appresolver.Resolver404",
        "Site": "cms.pages.appresolver.Site",
        "URLPattern": "cms.pages.appresolver.URLPattern",
        "URLResolver": "cms.pages.appresolver.URLResolver",
        "apphook_pool": "cms.pages.appresolver.apphook_pool",
        "applications_page_check": "cms.pages.appresolver.applications_page_check",
        "clear_app_resolvers": "cms.pages.appresolver.clear_app_resolvers",
        "get_app_patterns": "cms.pages.appresolver.get_app_patterns",
        "get_app_urls": "cms.pages.appresolver.get_app_urls",
        "get_current_site": "cms.pages.appresolver.get_current_site",
        "get_language": "cms.pages.appresolver.get_language",
        "get_language_list": "cms.pages.appresolver.get_language_list",
        "get_patterns_for_page_url": "cms.pages.appresolver.get_patterns_for_page_url",
        "import_module": "cms.pages.appresolver.import_module",
        "override": "cms.pages.appresolver.override",
        "recurse_patterns": "cms.pages.appresolver.recurse_patterns",
        "reverse": "cms.pages.appresolver.reverse",
    },
    since="6.0",
    fallback="cms.pages.appresolver",
)
