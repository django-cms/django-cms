"""Moved to :mod:`cms.core.plugin_processors`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "mark_safe": "cms.core.plugin_processors.mark_safe",
        "mark_safe_plugin_processor": "cms.core.plugin_processors.mark_safe_plugin_processor",
        "plugin_meta_context_processor": "cms.core.plugin_processors.plugin_meta_context_processor",
    },
    since="6.0",
    fallback="cms.core.plugin_processors",
)
