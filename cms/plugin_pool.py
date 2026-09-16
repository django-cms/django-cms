"""Moved to :mod:`cms.core.plugin_pool`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "CMSPluginBase": "cms.core.plugin_pool.CMSPluginBase",
        "ImproperlyConfigured": "cms.core.plugin_pool.ImproperlyConfigured",
        "Placeholder": "cms.core.plugin_pool.Placeholder",
        "PluginAlreadyRegistered": "cms.core.plugin_pool.PluginAlreadyRegistered",
        "PluginNotRegistered": "cms.core.plugin_pool.PluginNotRegistered",
        "PluginPool": "cms.core.plugin_pool.PluginPool",
        "TemplateDoesNotExist": "cms.core.plugin_pool.TemplateDoesNotExist",
        "TemplateSyntaxError": "cms.core.plugin_pool.TemplateSyntaxError",
        "URLResolver": "cms.core.plugin_pool.URLResolver",
        "activate": "cms.core.plugin_pool.activate",
        "attrgetter": "cms.core.plugin_pool.attrgetter",
        "autodiscover_modules": "cms.core.plugin_pool.autodiscover_modules",
        "cached_property": "cms.core.plugin_pool.cached_property",
        "deactivate_all": "cms.core.plugin_pool.deactivate_all",
        "defaultdict": "cms.core.plugin_pool.defaultdict",
        "fnmatch": "cms.core.plugin_pool.fnmatch",
        "force_str": "cms.core.plugin_pool.force_str",
        "get_language": "cms.core.plugin_pool.get_language",
        "include": "cms.core.plugin_pool.include",
        "lazy": "cms.core.plugin_pool.lazy",
        "lru_cache": "cms.core.plugin_pool.lru_cache",
        "models": "cms.core.plugin_pool.models",
        "normalize_name": "cms.core.plugin_pool.normalize_name",
        "plugin_pool": "cms.core.plugin_pool.plugin_pool",
        "re_path": "cms.core.plugin_pool.re_path",
        "slugify": "cms.core.plugin_pool.slugify",
    },
    since="6.0",
    fallback="cms.core.plugin_pool",
)
