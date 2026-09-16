"""Moved to :mod:`cms.core.plugin_base`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "CMSPlugin": "cms.core.plugin_base.CMSPlugin",
        "CMSPluginBase": "cms.core.plugin_base.CMSPluginBase",
        "CMSPluginBaseMetaclass": "cms.core.plugin_base.CMSPluginBaseMetaclass",
        "Callable": "cms.core.plugin_base.Callable",
        "Context": "cms.core.plugin_base.Context",
        "HttpRequest": "cms.core.plugin_base.HttpRequest",
        "HttpResponse": "cms.core.plugin_base.HttpResponse",
        "ImproperlyConfigured": "cms.core.plugin_base.ImproperlyConfigured",
        "ObjectDoesNotExist": "cms.core.plugin_base.ObjectDoesNotExist",
        "Placeholder": "cms.core.plugin_base.Placeholder",
        "PluginMenuItem": "cms.core.plugin_base.PluginMenuItem",
        "RemovedInDjangoCMS70Warning": "cms.core.plugin_base.RemovedInDjangoCMS70Warning",
        "SubClassNeededError": "cms.core.plugin_base.SubClassNeededError",
        "TemplateResponse": "cms.core.plugin_base.TemplateResponse",
        "ValidationError": "cms.core.plugin_base.ValidationError",
        "admin": "cms.core.plugin_base.admin",
        "conditional_escape": "cms.core.plugin_base.conditional_escape",
        "escapejs": "cms.core.plugin_base.escapejs",
        "fnmatch": "cms.core.plugin_base.fnmatch",
        "force_str": "cms.core.plugin_base.force_str",
        "forms": "cms.core.plugin_base.forms",
        "get_cms_setting": "cms.core.plugin_base.get_cms_setting",
        "get_plugin_tree": "cms.core.plugin_base.get_plugin_tree",
        "gettext": "cms.core.plugin_base.gettext",
        "json": "cms.core.plugin_base.json",
        "lazy": "cms.core.plugin_base.lazy",
        "lru_cache": "cms.core.plugin_base.lru_cache",
        "mark_safe": "cms.core.plugin_base.mark_safe",
        "messages": "cms.core.plugin_base.messages",
        "models": "cms.core.plugin_base.models",
        "operations": "cms.core.plugin_base.operations",
        "re": "cms.core.plugin_base.re",
        "smart_str": "cms.core.plugin_base.smart_str",
        "template_slot_caching": "cms.core.plugin_base.template_slot_caching",
        "warnings": "cms.core.plugin_base.warnings",
    },
    since="6.0",
    fallback="cms.core.plugin_base",
)
