"""Moved to :mod:`cms.core.plugins`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "CMSPlugin": "cms.core.plugins.CMSPlugin",
        "CMSPluginBase": "cms.core.plugins.CMSPluginBase",
        "HttpRequest": "cms.core.plugins.HttpRequest",
        "Iterable": "cms.core.plugins.Iterable",
        "OrderedDict": "cms.core.plugins.OrderedDict",
        "PLUGIN_ITERATOR_CHUNK_SIZE": "cms.core.plugins.PLUGIN_ITERATOR_CHUNK_SIZE",
        "PluginLimitReached": "cms.core.plugins.PluginLimitReached",
        "Sequence": "cms.core.plugins.Sequence",
        "assign_plugins": "cms.core.plugins.assign_plugins",
        "copy_plugins_to_placeholder": "cms.core.plugins.copy_plugins_to_placeholder",
        "create_default_plugins": "cms.core.plugins.create_default_plugins",
        "deepcopy": "cms.core.plugins.deepcopy",
        "defaultdict": "cms.core.plugins.defaultdict",
        "deque": "cms.core.plugins.deque",
        "downcast_plugins": "cms.core.plugins.downcast_plugins",
        "get_bound_plugins": "cms.core.plugins.get_bound_plugins",
        "get_language_from_request": "cms.core.plugins.get_language_from_request",
        "get_placeholder_conf": "cms.core.plugins.get_placeholder_conf",
        "get_plugin_class": "cms.core.plugins.get_plugin_class",
        "get_plugin_disallowed_in_slot": "cms.core.plugins.get_plugin_disallowed_in_slot",
        "get_plugin_model": "cms.core.plugins.get_plugin_model",
        "get_plugin_restrictions": "cms.core.plugins.get_plugin_restrictions",
        "get_plugins": "cms.core.plugins.get_plugins",
        "get_plugins_as_layered_tree": "cms.core.plugins.get_plugins_as_layered_tree",
        "has_plugin_permission": "cms.core.plugins.has_plugin_permission",
        "has_reached_plugin_limit": "cms.core.plugins.has_reached_plugin_limit",
        "itemgetter": "cms.core.plugins.itemgetter",
        "logger": "cms.core.plugins.logger",
        "logging": "cms.core.plugins.logging",
        "models": "cms.core.plugins.models",
        "plugin_pool": "cms.core.plugins.plugin_pool",
        "starmap": "cms.core.plugins.starmap",
        "sys": "cms.core.plugins.sys",
        "transaction": "cms.core.plugins.transaction",
    },
    since="6.0",
    fallback="cms.core.plugins",
)
