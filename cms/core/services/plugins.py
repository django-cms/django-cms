"""Placeholder and plugin operations, callable without an HttpRequest.

Every function here follows the shape the placeholder admin established:

1. emit the pre-operation signal and keep the token,
2. call the model primitive (``Placeholder.move_plugin`` and friends),
3. invalidate the affected placeholder caches,
4. emit the post-operation signal with the same token,
5. return the changed object.

**Permission checks are the caller's responsibility, and nothing here enforces
them.** Calling a service directly performs the operation for any user, or for
no user at all -- there is no check to fail and no error to catch. Enforcement
lives in the admin's ``has_*_permission`` methods, which are documented,
overridable hooks that djangocms-versioning and other packages replace; moving
them here without a permission backend would silently drop those overrides.

Until step 6 of the refactor supplies that backend, treat these functions as
privileged: call them from code that has already decided the user may act, and
do not expose them through a new entry point (a REST view, a command, a wizard)
without checking first.
"""

from __future__ import annotations

import uuid

from cms import operations
from cms.models import CMSPlugin, PlaceholderReference
from cms.shared.operations import OperationContext
from cms.signals import post_placeholder_operation, pre_placeholder_operation
from cms.utils.plugins import copy_plugins_to_placeholder

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


def _start(operation: str, context: OperationContext, sender, **kwargs) -> str:
    """Announce an operation about to happen and return its correlation token.

    The token is generated even when signals are silenced, so a caller can always
    pair its pre and post calls.
    """
    token = str(uuid.uuid4())
    if context.emit_signals:
        pre_placeholder_operation.send(
            sender=sender,
            operation=operation,
            request=context.request,
            user=context.user,
            language=context.language,
            token=token,
            origin=context.origin,
            **kwargs,
        )
    return token


def _finish(operation: str, context: OperationContext, token: str, sender, **kwargs) -> None:
    if not context.emit_signals:
        return
    post_placeholder_operation.send(
        sender=sender,
        operation=operation,
        request=context.request,
        user=context.user,
        language=context.language,
        token=token,
        origin=context.origin,
        **kwargs,
    )


def move_plugin(
    plugin: CMSPlugin,
    target_position: int,
    target_placeholder=None,
    target_parent=None,
    *,
    context: OperationContext,
    sender=None,
) -> CMSPlugin:
    """Move ``plugin`` to ``target_position``, optionally into another placeholder."""
    language = plugin.language
    source_placeholder = plugin.placeholder
    source_language = plugin.language
    source_parent_id = plugin.parent_id
    target_parent_id = target_parent.pk if target_parent else None

    signal_kwargs = {
        "plugin": plugin,
        "source_language": source_language,
        "source_placeholder": source_placeholder,
        "source_parent_id": source_parent_id,
        "target_language": language,
        "target_placeholder": (target_placeholder or source_placeholder),
        "target_parent_id": target_parent_id,
    }
    token = _start(operations.MOVE_PLUGIN, context, sender, **signal_kwargs)

    source_placeholder.move_plugin(
        plugin=plugin,
        target_position=target_position,
        target_placeholder=target_placeholder,
        target_plugin=target_parent,
    )

    # Refresh plugin to get new position values
    updated_plugin = plugin.reload()
    if target_placeholder:
        target_placeholder.clear_cache(language)
    source_placeholder.clear_cache(language)

    signal_kwargs["plugin"] = updated_plugin.get_bound_plugin()
    _finish(operations.MOVE_PLUGIN, context, token, sender, **signal_kwargs)
    return updated_plugin


def cut_plugin(
    plugin: CMSPlugin,
    target_language: str,
    target_placeholder,
    *,
    context: OperationContext,
    sender=None,
) -> CMSPlugin:
    """Move ``plugin`` into the clipboard, emptying whatever was there."""
    source_placeholder = plugin.placeholder
    source_language = plugin.language
    source_parent_id = plugin.parent_id
    source_order = source_placeholder.get_plugin_tree_order(source_language, source_parent_id)

    token = _start(
        operations.CUT_PLUGIN,
        context,
        sender,
        plugin=plugin,
        clipboard=target_placeholder,
        clipboard_language=target_language,
        source_language=source_language,
        source_placeholder=source_placeholder,
        source_parent_id=source_parent_id,
        source_order=source_order,
    )

    # Empty the clipboard
    target_placeholder.clear()
    source_placeholder.move_plugin(
        plugin,
        target_position=1,
        target_placeholder=target_placeholder,
        target_plugin=None,
    )
    source_placeholder.clear_cache(plugin.language)
    updated_plugin = plugin.reload()
    source_order = source_placeholder.get_plugin_tree_order(source_language, source_parent_id)

    _finish(
        operations.CUT_PLUGIN,
        context,
        token,
        sender,
        plugin=updated_plugin.get_bound_plugin(),
        clipboard=target_placeholder,
        clipboard_language=target_language,
        source_language=source_language,
        source_placeholder=source_placeholder,
        source_parent_id=source_parent_id,
        source_order=source_order,
    )
    return updated_plugin


def _make_room(target_placeholder, target_language: str, target_position: int, count: int) -> None:
    """Shift existing plugins aside so ``count`` plugins fit at ``target_position``."""
    target_last_plugin = target_placeholder.get_last_plugin(target_language)
    if target_last_plugin:
        target_placeholder._shift_plugin_positions(
            target_language,
            start=target_position,
            offset=target_last_plugin.position + count,
        )


def paste_plugin(
    plugin: CMSPlugin,
    target_language: str,
    target_placeholder,
    target_position: int,
    target_parent=None,
    *,
    context: OperationContext,
    sender=None,
) -> CMSPlugin:
    """Copy ``plugin`` and its descendants out of the clipboard into a placeholder."""
    plugins = [plugin] + list(plugin.get_descendants())
    target_parent_id = target_parent.pk if target_parent else None

    token = _start(
        operations.PASTE_PLUGIN,
        context,
        sender,
        plugin=plugin,
        target_language=target_language,
        target_placeholder=target_placeholder,
        target_parent_id=target_parent_id,
    )

    _make_room(target_placeholder, target_language, target_position, len(plugins))

    new_plugins = copy_plugins_to_placeholder(
        plugins,
        placeholder=target_placeholder,
        language=target_language,
        root_plugin=target_parent,
        start_positions={target_language: target_position},
    )
    root_plugin = new_plugins[0]
    target_placeholder.clear_cache(target_language)

    # Fetch from db to update position and other tree values
    root_plugin.refresh_from_db()

    _finish(
        operations.PASTE_PLUGIN,
        context,
        token,
        sender,
        plugin=root_plugin.get_bound_plugin(),
        target_language=target_language,
        target_placeholder=target_placeholder,
        target_parent_id=target_parent_id,
    )
    return root_plugin


def paste_placeholder(
    plugin: CMSPlugin,
    target_language: str,
    target_placeholder,
    target_position: int,
    *,
    context: OperationContext,
    sender=None,
) -> list[CMSPlugin]:
    """Copy a whole clipboard placeholder's plugins into a placeholder."""
    plugins = plugin.placeholder_ref.get_plugins_list()

    token = _start(
        operations.PASTE_PLACEHOLDER,
        context,
        sender,
        plugins=plugins,
        target_language=target_language,
        target_placeholder=target_placeholder,
    )

    _make_room(target_placeholder, target_language, target_position, len(plugins))

    new_plugins = copy_plugins_to_placeholder(
        plugins,
        placeholder=target_placeholder,
        language=target_language,
        start_positions={target_language: target_position},
    )
    new_plugin_ids = (new.pk for new in new_plugins)
    target_placeholder.clear_cache(target_language)

    new_plugins = list(CMSPlugin.objects.filter(pk__in=new_plugin_ids).select_related("placeholder"))

    _finish(
        operations.PASTE_PLACEHOLDER,
        context,
        token,
        sender,
        plugins=new_plugins,
        target_language=target_language,
        target_placeholder=target_placeholder,
    )
    return new_plugins


def copy_plugin_to_clipboard(
    source_plugin: CMSPlugin,
    target_placeholder,
    target_language: str,
    *,
    context: OperationContext,
) -> CMSPlugin:
    """Copy a plugin subtree into the clipboard.

    Emits no operation signals, matching the behaviour this replaced: the
    clipboard is private scratch space, not content.
    """
    old_plugins = [source_plugin] + list(source_plugin.get_descendants())

    # Empty the clipboard
    target_placeholder.clear()

    copied_plugins = copy_plugins_to_placeholder(
        old_plugins,
        placeholder=target_placeholder,
        language=target_language,
    )
    return copied_plugins[0]


def copy_placeholder_to_clipboard(
    source_placeholder,
    target_placeholder,
    source_language: str,
    target_language: str,
    *,
    context: OperationContext,
) -> PlaceholderReference:
    """Copy a whole placeholder into the clipboard, wrapped in one reference plugin.

    The reference plugin creates a blank placeholder of its own to hold the
    copies, so that everything pasted lands under a single plugin. Emits no
    operation signals, as above.
    """
    old_plugins = source_placeholder.get_plugins_list(language=source_language)

    # Empty the clipboard
    target_placeholder.clear()

    reference = PlaceholderReference.objects.create(
        name=source_placeholder.get_label(),
        plugin_type="PlaceholderPlugin",
        language=target_language,
        placeholder=target_placeholder,
    )
    copy_plugins_to_placeholder(
        old_plugins,
        placeholder=reference.placeholder_ref,
        language=target_language,
    )
    return reference


def add_plugins_from_placeholder(
    source_placeholder,
    target_placeholder,
    source_language: str,
    target_language: str,
    *,
    context: OperationContext,
    sender=None,
) -> list[CMSPlugin]:
    """Copy a placeholder's plugins into another placeholder ("copy from language")."""
    old_plugins = source_placeholder.get_plugins_list(language=source_language)
    target_tree_order = target_placeholder.get_plugin_tree_order(language=target_language, parent_id=None)

    token = _start(
        operations.ADD_PLUGINS_FROM_PLACEHOLDER,
        context,
        sender,
        plugins=old_plugins,
        source_language=source_language,
        source_placeholder=source_placeholder,
        target_language=target_language,
        target_placeholder=target_placeholder,
        target_order=target_tree_order,
    )

    copied_plugins = copy_plugins_to_placeholder(old_plugins, target_placeholder, language=target_language)
    new_plugin_ids = (new.pk for new in copied_plugins)

    target_placeholder.clear_cache(target_language)

    new_plugins = list(CMSPlugin.objects.filter(pk__in=new_plugin_ids))
    target_tree_order = target_placeholder.get_plugin_tree_order(language=target_language, parent_id=None)

    _finish(
        operations.ADD_PLUGINS_FROM_PLACEHOLDER,
        context,
        token,
        sender,
        plugins=new_plugins,
        source_language=source_language,
        source_placeholder=source_placeholder,
        target_language=target_language,
        target_placeholder=target_placeholder,
        target_order=target_tree_order,
    )
    return new_plugins


def delete_plugin(plugin: CMSPlugin, *, context: OperationContext, sender=None) -> list[int]:
    """Delete a plugin and return the placeholder's resulting plugin tree order."""
    placeholder = plugin.placeholder
    tree_order = placeholder.get_plugin_tree_order(language=plugin.language)

    token = _start(
        operations.DELETE_PLUGIN,
        context,
        sender,
        plugin=plugin,
        placeholder=placeholder,
        tree_order=tree_order,
    )

    placeholder.delete_plugin(plugin)
    placeholder.clear_cache(plugin.language)
    tree_order = placeholder.get_plugin_tree_order(language=plugin.language)

    _finish(
        operations.DELETE_PLUGIN,
        context,
        token,
        sender,
        plugin=plugin,
        placeholder=placeholder,
        tree_order=tree_order,
    )
    return tree_order


def clear_placeholder(
    placeholder,
    language: str | None,
    *,
    context: OperationContext,
    site_id: int | None = None,
    sender=None,
) -> None:
    """Remove every plugin in ``language`` from ``placeholder``."""
    plugins = placeholder.get_plugins_list(language)

    token = _start(
        operations.CLEAR_PLACEHOLDER,
        context,
        sender,
        plugins=plugins,
        placeholder=placeholder,
    )

    placeholder.clear(language)
    placeholder.clear_cache(language, site_id=site_id)

    _finish(
        operations.CLEAR_PLACEHOLDER,
        context,
        token,
        sender,
        plugins=plugins,
        placeholder=placeholder,
    )
