"""Business operations on placeholders and plugins, without an HttpRequest.

Each service is the wrapper that used to live in ``PlaceholderAdmin``: emit the
pre-operation signal, call the model primitive, invalidate caches, emit the
post-operation signal, return the changed object. The model layer keeps the
mechanics (``Placeholder.move_plugin`` and friends); what moved up here is the
orchestration that the admin was the only way to reach.

Permission enforcement is the caller's responsibility, and nothing here enforces
it. The admin's ``has_*_permission`` methods are documented, overridable hooks
that djangocms-versioning and others replace, so they stay where subclasses can
still reach them. Step 6 of the refactor gives services a permission backend of
their own; until then these functions are privileged and must not be exposed
through a new entry point without a check in front of them.
"""

from cms.core.services.plugins import (
    add_plugins_from_placeholder,
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
    "add_plugins_from_placeholder",
    "clear_placeholder",
    "copy_placeholder_to_clipboard",
    "copy_plugin_to_clipboard",
    "cut_plugin",
    "delete_plugin",
    "move_plugin",
    "paste_placeholder",
    "paste_plugin",
]
