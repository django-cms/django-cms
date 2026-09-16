"""Moved to :mod:`cms.core.models.plugin`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "BoundRenderMeta": "cms.core.models.plugin.BoundRenderMeta",
        "CMSPlugin": "cms.core.models.plugin.CMSPlugin",
        "DontUsePageAttributeWarning": "cms.core.models.plugin.DontUsePageAttributeWarning",
        "ModelBase": "cms.core.models.plugin.ModelBase",
        "ObjectDoesNotExist": "cms.core.models.plugin.ObjectDoesNotExist",
        "Placeholder": "cms.core.models.plugin.Placeholder",
        "PluginModelBase": "cms.core.models.plugin.PluginModelBase",
        "QuerySet": "cms.core.models.plugin.QuerySet",
        "RemovedInDjangoCMS60Warning": "cms.core.models.plugin.RemovedInDjangoCMS60Warning",
        "admin_reverse": "cms.core.models.plugin.admin_reverse",
        "annotations": "cms.core.models.plugin.annotations",
        "cache": "cms.core.models.plugin.cache",
        "cached_property": "cms.core.models.plugin.cached_property",
        "connection": "cms.core.models.plugin.connection",
        "connections": "cms.core.models.plugin.connections",
        "date": "cms.core.models.plugin.date",
        "force_str": "cms.core.models.plugin.force_str",
        "get_cms_setting": "cms.core.models.plugin.get_cms_setting",
        "get_plugin_media_path": "cms.core.models.plugin.get_plugin_media_path",
        "models": "cms.core.models.plugin.models",
        "os": "cms.core.models.plugin.os",
        "re": "cms.core.models.plugin.re",
        "router": "cms.core.models.plugin.router",
        "timezone": "cms.core.models.plugin.timezone",
        "warnings": "cms.core.models.plugin.warnings",
    },
    since="6.0",
    fallback="cms.core.models.plugin",
)
