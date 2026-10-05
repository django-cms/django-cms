"""Business operations on placeholders and plugins, without an HttpRequest.

Each service is the wrapper that used to live in ``PlaceholderAdmin``: emit the
pre-operation signal, call the model primitive, invalidate caches, emit the
post-operation signal, return the changed object. The model layer keeps the
mechanics (``Placeholder.move_plugin`` and friends); what moved up here is the
orchestration that the admin was the only way to reach.

Every service enforces permissions through a backend
(:mod:`cms.core.services.permissions`), so an operation reached from outside the
admin is checked the same way. The placeholder admin passes ``permissions=``, an
adapter that asks its overridable ``has_*_permission`` methods, which
djangocms-versioning and others replace; a ``permissions`` contract replaces the
backend for every caller.
"""

from cms.core.services.plugins import (
    add_plugin,
    add_plugins_from_placeholder,
    change_plugin,
    clear_placeholder,
    copy_placeholder_to_clipboard,
    copy_plugin_to_clipboard,
    cut_plugin,
    delete_plugin,
    move_plugin,
    paste_placeholder,
    paste_plugin,
)

__all__ = [
    "add_plugin",
    "add_plugins_from_placeholder",
    "change_plugin",
    "clear_placeholder",
    "copy_placeholder_to_clipboard",
    "copy_plugin_to_clipboard",
    "cut_plugin",
    "delete_plugin",
    "move_plugin",
    "paste_placeholder",
    "paste_plugin",
]
