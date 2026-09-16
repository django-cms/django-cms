"""Moved to :mod:`cms.core.placeholders`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "BlockNode": "cms.core.placeholders.BlockNode",
        "Context": "cms.core.placeholders.Context",
        "DuplicatePlaceholderWarning": "cms.core.placeholders.DuplicatePlaceholderWarning",
        "EmptyPageContent": "cms.core.placeholders.EmptyPageContent",
        "ExtendsNode": "cms.core.placeholders.ExtendsNode",
        "ImproperlyConfigured": "cms.core.placeholders.ImproperlyConfigured",
        "IncludeNode": "cms.core.placeholders.IncludeNode",
        "NodeList": "cms.core.placeholders.NodeList",
        "OrderedDict": "cms.core.placeholders.OrderedDict",
        "Placeholder": "cms.core.placeholders.Placeholder",
        "RANGE_START": "cms.core.placeholders.RANGE_START",
        "TYPE_CHECKING": "cms.core.placeholders.TYPE_CHECKING",
        "Template": "cms.core.placeholders.Template",
        "TemplateDoesNotExist": "cms.core.placeholders.TemplateDoesNotExist",
        "TemplateSyntaxError": "cms.core.placeholders.TemplateSyntaxError",
        "Variable": "cms.core.placeholders.Variable",
        "VariableNode": "cms.core.placeholders.VariableNode",
        "cache": "cms.core.placeholders.cache",
        "connection": "cms.core.placeholders.connection",
        "defaultdict": "cms.core.placeholders.defaultdict",
        "engines": "cms.core.placeholders.engines",
        "get_cms_setting": "cms.core.placeholders.get_cms_setting",
        "get_context": "cms.core.placeholders.get_context",
        "get_declared_placeholders_for_obj": "cms.core.placeholders.get_declared_placeholders_for_obj",
        "get_placeholder_conf": "cms.core.placeholders.get_placeholder_conf",
        "get_placeholder_from_slot": "cms.core.placeholders.get_placeholder_from_slot",
        "get_placeholders": "cms.core.placeholders.get_placeholders",
        "get_template": "cms.core.placeholders.get_template",
        "get_toolbar_plugin_struct": "cms.core.placeholders.get_toolbar_plugin_struct",
        "get_varname": "cms.core.placeholders.get_varname",
        "models": "cms.core.placeholders.models",
        "operator": "cms.core.placeholders.operator",
        "os": "cms.core.placeholders.os",
        "rescan_placeholders_for_obj": "cms.core.placeholders.rescan_placeholders_for_obj",
        "restore_sekizai_context": "cms.core.placeholders.restore_sekizai_context",
        "settings": "cms.core.placeholders.settings",
        "validate_placeholder_name": "cms.core.placeholders.validate_placeholder_name",
        "warnings": "cms.core.placeholders.warnings",
    },
    since="6.0",
    fallback="cms.core.placeholders",
)
