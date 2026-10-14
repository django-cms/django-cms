"""Placeholder and plugin operations, callable without an HttpRequest.

Every service runs in the :func:`~cms.shared.operations.operation` frame:

1. run the checks registered for the operation (:mod:`cms.core.checks` and any
   an app adds), raising ``PermissionDenied``, ``OperationBlocked`` or
   ``ValidationError``,
2. emit the pre-operation signal,
3. call the model primitive (``Placeholder.move_plugin`` and friends) and
   invalidate the affected placeholder caches,
4. emit the post-operation signal with the same token,
5. return the changed object.

The permission checks ask a backend (:mod:`cms.core.permissions`), so a
caller reaching an operation from outside the admin is checked the same way. Pass
``permissions=`` to supply a different backend for one call -- the placeholder
admin does this, handing over an adapter that routes each predicate back through
its own overridable ``has_*_permission`` hooks -- or export a ``permissions``
contract to replace it for every caller at once.
"""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils.translation import gettext_lazy as _lazy

from cms import operations
from cms.core import checks as core_checks  # noqa: F401  -- registers the plugin operation checks
from cms.core.permissions import get_permissions
from cms.core.plugin_pool import plugin_pool
from cms.core.plugins import copy_plugins_to_placeholder
from cms.models import CMSPlugin, PlaceholderReference
from cms.operations import Argument, Operation, register_operation
from cms.shared.checks import run_checks
from cms.shared.operations import OperationContext, operation
from cms.signals import PLACEHOLDER_OPERATION_SIGNALS, post_placeholder_operation, pre_placeholder_operation

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


def _guard(permissions, context: OperationContext):
    return permissions if permissions is not None else get_permissions(context.user)


def _start(operation: str, context: OperationContext, sender, **kwargs) -> str:
    """Announce an operation about to happen and return its correlation token.

    For callers that cannot use the :func:`~cms.shared.operations.operation`
    frame, such as ``CMSPluginBase.save_model()``. The token is generated even
    when signals are silenced, so a caller can always pair its pre and post calls.
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


def _resolve_position(placeholder, language: str, position, target):
    """The parent and absolute tree position a new plugin gets.

    ``position`` is ``"first-child"`` or ``"last-child"`` of ``target`` (or of the
    placeholder without one), ``"left"`` or ``"right"`` of ``target`` as a
    sibling, or an absolute tree position with ``target`` as the parent.
    """
    if isinstance(position, int):
        return target, position
    if target is None:
        if position == "first-child":
            return None, 1
        if position == "last-child":
            return None, placeholder.get_next_plugin_position(language, insert_order="last")
    elif position in ("first-child", "last-child"):
        insert_order = "first" if position == "first-child" else "last"
        return target, placeholder.get_next_plugin_position(language, parent=target, insert_order=insert_order)
    elif position == "left":
        return target.parent, target.position
    elif position == "right":
        return target.parent, target.position + 1 + target._get_descendants_count()
    raise ValueError(f"Unsupported plugin position {position!r} (target: {target!r}).")


def add_plugin(
    placeholder,
    plugin_type: str,
    language: str,
    data: dict | None = None,
    *,
    position="last-child",
    target=None,
    context: OperationContext,
    permissions=None,
    form=None,
    sender=None,
) -> CMSPlugin:
    """Add a plugin of ``plugin_type`` to ``placeholder`` and return it.

    ``position`` is ``"first-child"`` or ``"last-child"`` of ``target`` (or of the
    placeholder without a target), ``"left"`` or ``"right"`` of ``target`` as a
    sibling, or an absolute tree position with ``target`` as the parent.

    ``data`` is cleaned by the plugin's
    :meth:`~cms.core.plugin_base.CMSPluginBase.clean_plugin_data`, as the
    plugin's form would. A caller that already validated a form for the plugin --
    the admin -- passes it as ``form`` instead, and saves its many-to-many data
    itself.

    :raises ~django.core.exceptions.ValidationError: if the plugin type is unknown, not allowed in the
        placeholder's slot, the placeholder has reached its plugin limit, ``target`` is not in the placeholder
        and language, or ``data`` is not valid.
    """
    with transaction.atomic():
        run_checks(
            operations.ADD_PLUGIN,
            context,
            placeholder=placeholder,
            plugin_type=plugin_type,
            language=language,
            data=data,
            position=position,
            target=target,
            permissions=_guard(permissions, context),
            instance=form.instance if form is not None else None,
        )
        save_m2m = form is None
        if form is None:
            plugin_class = plugin_pool.get_plugin(plugin_type)
            form = plugin_class.clean_plugin_data(placeholder.source, data or {})
        plugin = form.save(commit=False)
        parent, tree_position = _resolve_position(placeholder, language, position, target)
        plugin.placeholder = placeholder
        plugin.language = language
        plugin.plugin_type = plugin_type
        plugin.parent = parent
        plugin.position = tree_position

        # The checks ran above, before the data was cleaned: the pre signal
        # announces the plugin as it will be saved.
        with operation(
            operations.ADD_PLUGIN,
            context,
            signals=PLACEHOLDER_OPERATION_SIGNALS,
            sender=sender,
            plugin=plugin,
            placeholder=placeholder,
            tree_order=placeholder.get_plugin_tree_order(language, plugin.parent_id),
        ) as signal_kwargs:
            plugin = placeholder.add_plugin(plugin)
            if save_m2m:
                form.save_m2m()
            placeholder.clear_cache(language)
            signal_kwargs["plugin"] = plugin
            signal_kwargs["tree_order"] = placeholder.get_plugin_tree_order(language, plugin.parent_id)
    return plugin


def change_plugin(
    plugin: CMSPlugin,
    data: dict | None = None,
    *,
    context: OperationContext,
    permissions=None,
    form=None,
    sender=None,
) -> CMSPlugin:
    """Change ``plugin`` with ``data`` and return it.

    ``data`` holds the fields that change; it is cleaned by the plugin's
    :meth:`~cms.core.plugin_base.CMSPluginBase.clean_plugin_data`. A caller that
    already validated a form for the plugin passes it as ``form`` instead, and
    saves its many-to-many data itself.

    :raises ~django.core.exceptions.ValidationError: if ``data`` is not valid.
    """
    placeholder = plugin.placeholder
    with transaction.atomic():
        run_checks(
            operations.CHANGE_PLUGIN,
            context,
            plugin=plugin,
            data=data,
            permissions=_guard(permissions, context),
        )
        plugin_class = plugin_pool.get_plugin(plugin.plugin_type)
        old_plugin = plugin_class.model.objects.get(pk=plugin.pk)
        save_m2m = form is None
        if form is None:
            instance = plugin if isinstance(plugin, plugin_class.model) else plugin.get_bound_plugin()
            form = plugin_class.clean_plugin_data(placeholder.source, data or {}, instance=instance)
        new_plugin = form.save(commit=False)

        with operation(
            operations.CHANGE_PLUGIN,
            context,
            signals=PLACEHOLDER_OPERATION_SIGNALS,
            sender=sender,
            old_plugin=old_plugin,
            new_plugin=new_plugin,
            placeholder=placeholder,
        ):
            new_plugin.save()
            if save_m2m:
                form.save_m2m()
            placeholder.clear_cache(new_plugin.language)
    return new_plugin


def move_plugin(
    plugin: CMSPlugin,
    target_position: int,
    target_placeholder=None,
    target_parent=None,
    *,
    context: OperationContext,
    permissions=None,
    sender=None,
) -> CMSPlugin:
    """Move ``plugin`` to ``target_position``, optionally into another placeholder.

    :raises ~django.core.exceptions.ValidationError: if ``target_parent`` is not in the target placeholder and
        the plugin's language, or is the plugin itself or one of its descendants, or if the plugin or one of its
        descendants is not allowed in the target placeholder's slot.
    """
    language = plugin.language
    source_placeholder = plugin.placeholder

    with operation(
        operations.MOVE_PLUGIN,
        context,
        checks={
            "plugin": plugin,
            "target_position": target_position,
            "target_placeholder": target_placeholder,
            "target_parent": target_parent,
            "permissions": _guard(permissions, context),
        },
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugin=plugin,
        source_language=language,
        source_placeholder=source_placeholder,
        source_parent_id=plugin.parent_id,
        target_language=language,
        target_placeholder=target_placeholder or source_placeholder,
        target_parent_id=target_parent.pk if target_parent else None,
    ) as signal_kwargs:
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
    return updated_plugin


def cut_plugin(
    plugin: CMSPlugin,
    target_language: str,
    target_placeholder,
    *,
    context: OperationContext,
    permissions=None,
    sender=None,
) -> CMSPlugin:
    """Move ``plugin`` into the clipboard, emptying whatever was there."""
    source_placeholder = plugin.placeholder
    source_language = plugin.language
    source_parent_id = plugin.parent_id

    with operation(
        operations.CUT_PLUGIN,
        context,
        checks={
            "plugin": plugin,
            "target_language": target_language,
            "target_placeholder": target_placeholder,
            "permissions": _guard(permissions, context),
        },
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugin=plugin,
        clipboard=target_placeholder,
        clipboard_language=target_language,
        source_language=source_language,
        source_placeholder=source_placeholder,
        source_parent_id=source_parent_id,
        source_order=source_placeholder.get_plugin_tree_order(source_language, source_parent_id),
    ) as signal_kwargs:
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

        signal_kwargs["plugin"] = updated_plugin.get_bound_plugin()
        signal_kwargs["source_order"] = source_placeholder.get_plugin_tree_order(source_language, source_parent_id)
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
    permissions=None,
    sender=None,
) -> CMSPlugin:
    """Copy ``plugin`` and its descendants out of the clipboard into a placeholder.

    :raises ~django.core.exceptions.ValidationError: if ``target_parent`` is not in ``target_placeholder`` and
        ``target_language``, or if one of the plugins is not allowed in the target placeholder's slot.
    """
    plugins = [plugin, *plugin.get_descendants()]

    with operation(
        operations.PASTE_PLUGIN,
        context,
        checks={
            "plugin": plugin,
            "target_language": target_language,
            "target_placeholder": target_placeholder,
            "target_position": target_position,
            "target_parent": target_parent,
            "permissions": _guard(permissions, context),
            "plugins": plugins,
        },
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugin=plugin,
        target_language=target_language,
        target_placeholder=target_placeholder,
        target_parent_id=target_parent.pk if target_parent else None,
    ) as signal_kwargs:
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
        signal_kwargs["plugin"] = root_plugin.get_bound_plugin()
    return root_plugin


def paste_placeholder(
    plugin: CMSPlugin,
    target_language: str,
    target_placeholder,
    target_position: int,
    *,
    context: OperationContext,
    permissions=None,
    sender=None,
) -> list[CMSPlugin]:
    """Copy a whole clipboard placeholder's plugins into a placeholder.

    :raises ~django.core.exceptions.ValidationError: if one of the plugins is not allowed in the target
        placeholder's slot.
    """
    plugins = plugin.placeholder_ref.get_plugins_list()

    with operation(
        operations.PASTE_PLACEHOLDER,
        context,
        checks={
            "plugin": plugin,
            "target_language": target_language,
            "target_placeholder": target_placeholder,
            "target_position": target_position,
            "permissions": _guard(permissions, context),
            "plugins": plugins,
        },
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugins=plugins,
        target_language=target_language,
        target_placeholder=target_placeholder,
    ) as signal_kwargs:
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
        signal_kwargs["plugins"] = new_plugins
    return new_plugins


def copy_plugin_to_clipboard(
    source_plugin: CMSPlugin,
    target_placeholder,
    target_language: str,
    *,
    context: OperationContext,
    permissions=None,
) -> CMSPlugin:
    """Copy a plugin subtree into the clipboard.

    Emits no operation signals, matching the behaviour this replaced: the
    clipboard is private scratch space, not content.
    """
    old_plugins = [source_plugin, *source_plugin.get_descendants()]

    with operation(
        operations.COPY_PLUGIN_TO_CLIPBOARD,
        context,
        checks={
            "source_plugin": source_plugin,
            "target_placeholder": target_placeholder,
            "target_language": target_language,
            "permissions": _guard(permissions, context),
            "plugins": old_plugins,
        },
    ):
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
    permissions=None,
) -> PlaceholderReference:
    """Copy a whole placeholder into the clipboard, wrapped in one reference plugin.

    The reference plugin creates a blank placeholder of its own to hold the
    copies, so that everything pasted lands under a single plugin. Emits no
    operation signals, as above.
    """
    old_plugins = source_placeholder.get_plugins_list(language=source_language)

    with operation(
        operations.COPY_PLACEHOLDER_TO_CLIPBOARD,
        context,
        checks={
            "source_placeholder": source_placeholder,
            "target_placeholder": target_placeholder,
            "source_language": source_language,
            "target_language": target_language,
            "permissions": _guard(permissions, context),
            "plugins": old_plugins,
        },
    ):
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
    permissions=None,
    sender=None,
) -> list[CMSPlugin]:
    """Copy a placeholder's plugins into another placeholder ("copy from language").

    :raises ~django.core.exceptions.ValidationError: if one of the plugins is not allowed in the target
        placeholder's slot.
    """
    old_plugins = source_placeholder.get_plugins_list(language=source_language)

    with operation(
        operations.ADD_PLUGINS_FROM_PLACEHOLDER,
        context,
        checks={
            "source_placeholder": source_placeholder,
            "target_placeholder": target_placeholder,
            "source_language": source_language,
            "target_language": target_language,
            "permissions": _guard(permissions, context),
            "plugins": old_plugins,
        },
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugins=old_plugins,
        source_language=source_language,
        source_placeholder=source_placeholder,
        target_language=target_language,
        target_placeholder=target_placeholder,
        target_order=target_placeholder.get_plugin_tree_order(language=target_language, parent_id=None),
    ) as signal_kwargs:
        copied_plugins = copy_plugins_to_placeholder(old_plugins, target_placeholder, language=target_language)
        new_plugin_ids = (new.pk for new in copied_plugins)

        target_placeholder.clear_cache(target_language)

        new_plugins = list(CMSPlugin.objects.filter(pk__in=new_plugin_ids))
        signal_kwargs["plugins"] = new_plugins
        signal_kwargs["target_order"] = target_placeholder.get_plugin_tree_order(
            language=target_language, parent_id=None
        )
    return new_plugins


def delete_plugin(
    plugin: CMSPlugin, *, context: OperationContext, permissions=None, sender=None
) -> list[int]:
    """Delete a plugin and return the placeholder's resulting plugin tree order."""
    placeholder = plugin.placeholder

    with operation(
        operations.DELETE_PLUGIN,
        context,
        checks={"plugin": plugin, "permissions": _guard(permissions, context)},
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugin=plugin,
        placeholder=placeholder,
        tree_order=placeholder.get_plugin_tree_order(language=plugin.language),
    ) as signal_kwargs:
        placeholder.delete_plugin(plugin)
        placeholder.clear_cache(plugin.language)
        tree_order = placeholder.get_plugin_tree_order(language=plugin.language)
        signal_kwargs["tree_order"] = tree_order
    return tree_order


def clear_placeholder(
    placeholder,
    language: str | None,
    *,
    context: OperationContext,
    permissions=None,
    site_id: int | None = None,
    sender=None,
) -> None:
    """Remove every plugin in ``language`` from ``placeholder``."""
    with operation(
        operations.CLEAR_PLACEHOLDER,
        context,
        checks={"placeholder": placeholder, "language": language, "permissions": _guard(permissions, context)},
        signals=PLACEHOLDER_OPERATION_SIGNALS,
        sender=sender,
        plugins=placeholder.get_plugins_list(language),
        placeholder=placeholder,
    ):
        placeholder.clear(language)
        placeholder.clear_cache(language, site_id=site_id)


# -- operation registry -------------------------------------------------------
# Summaries are shown to editors and translated; descriptions are read by API
# schemas and assistant tool definitions and stay plain English.

for _declaration in (
    Operation(
        operations.ADD_PLUGIN,
        summary=_lazy("Add a plugin"),
        description=(
            "Add a plugin to a placeholder, at the top level or as a child of another plugin. "
            "Requires permission to add this plugin type. Refused if the object owning the "
            "placeholder may not be edited, or if the plugin is not allowed there."
        ),
        service=add_plugin,
        arguments=(
            Argument("placeholder", model="cms.Placeholder", description="The placeholder to add the plugin to."),
            Argument("plugin_type", type=str, description="The plugin's class name, e.g. \"TextPlugin\"."),
            Argument("language", type=str, description="The language of the plugin."),
            Argument(
                "data",
                type=dict,
                required=False,
                null=True,
                description="The plugin's field values, validated as by the plugin's form.",
            ),
            Argument(
                "position",
                type=(str, int),
                required=False,
                description=(
                    "\"first-child\" or \"last-child\" (the default) of target, or of the placeholder without "
                    "a target; \"left\" or \"right\" of target as a sibling; or a tree position with target as "
                    "the parent."
                ),
            ),
            Argument(
                "target",
                model="cms.CMSPlugin",
                required=False,
                null=True,
                description="The plugin the position is relative to.",
            ),
        ),
    ),
    Operation(
        operations.CHANGE_PLUGIN,
        summary=_lazy("Change a plugin"),
        description=(
            "Change the data of a plugin. Requires permission to change the plugin. Refused if the "
            "object owning the placeholder may not be edited, or if the data is not valid for the "
            "plugin."
        ),
        service=change_plugin,
        arguments=(
            Argument("plugin", model="cms.CMSPlugin", description="The plugin."),
            Argument(
                "data",
                type=dict,
                required=False,
                null=True,
                description="The field values that change, validated as by the plugin's form.",
            ),
        ),
    ),
    Operation(
        operations.MOVE_PLUGIN,
        summary=_lazy("Move a plugin within or between placeholders"),
        description=(
            "Move a plugin with its children to another position, parent or placeholder. Requires "
            "permission to move the plugin to the target placeholder. Refused if the parent is not "
            "in the target placeholder and language, or if the plugin would end up inside itself."
        ),
        service=move_plugin,
        arguments=(
            Argument("plugin", model="cms.CMSPlugin", description="The plugin."),
            Argument("target_position", type=int, description="The plugin's new position in the placeholder's tree."),
            Argument(
                "target_placeholder",
                model="cms.Placeholder",
                required=False,
                null=True,
                description="The placeholder to move to; the plugin's own if not given.",
            ),
            Argument(
                "target_parent",
                model="cms.CMSPlugin",
                required=False,
                null=True,
                description="The new parent plugin; none for the top level.",
            ),
        ),
    ),
    Operation(
        operations.CUT_PLUGIN,
        summary=_lazy("Cut a plugin to the clipboard"),
        description=(
            "Move a plugin with its children from its placeholder to the acting user's clipboard. "
            "Requires permission to delete the plugin from its placeholder."
        ),
        service=cut_plugin,
        arguments=(
            Argument("plugin", model="cms.CMSPlugin", description="The plugin."),
            Argument("target_language", type=str, description="The language of the clipboard."),
            Argument("target_placeholder", model="cms.Placeholder", description="The acting user's clipboard."),
        ),
    ),
    Operation(
        operations.PASTE_PLUGIN,
        summary=_lazy("Paste a plugin"),
        description=(
            "Copy a plugin with its children from the clipboard or another placeholder into a "
            "placeholder. Requires permission to read the source and to add the plugins to the "
            "target. Refused if the parent is not in the target placeholder and language."
        ),
        service=paste_plugin,
        arguments=(
            Argument("plugin", model="cms.CMSPlugin", description="The plugin to copy, with its descendants."),
            Argument("target_language", type=str, description="The language to paste into."),
            Argument("target_placeholder", model="cms.Placeholder", description="The placeholder to paste into."),
            Argument("target_position", type=int, description="The position of the copy in the placeholder's tree."),
            Argument(
                "target_parent",
                model="cms.CMSPlugin",
                required=False,
                null=True,
                description="The parent plugin of the copy; none for the top level.",
            ),
        ),
    ),
    Operation(
        operations.PASTE_PLACEHOLDER,
        summary=_lazy("Paste a copied placeholder"),
        description=(
            "Copy all plugins of a placeholder held on the clipboard into a placeholder. Requires "
            "permission to read the source and to add the plugins to the target."
        ),
        service=paste_placeholder,
        arguments=(
            Argument("plugin", model="cms.CMSPlugin", description="The placeholder reference plugin on the clipboard."),
            Argument("target_language", type=str, description="The language to paste into."),
            Argument("target_placeholder", model="cms.Placeholder", description="The placeholder to paste into."),
            Argument("target_position", type=int, description="The position of the first copy in the placeholder's tree."),
        ),
    ),
    Operation(
        operations.ADD_PLUGINS_FROM_PLACEHOLDER,
        summary=_lazy("Copy plugins from another placeholder"),
        description=(
            "Copy all plugins of one placeholder and language into another placeholder and "
            "language. Requires permission to read the source and to add the plugins to the target."
        ),
        service=add_plugins_from_placeholder,
        arguments=(
            Argument("source_placeholder", model="cms.Placeholder", description="The placeholder to copy from."),
            Argument("target_placeholder", model="cms.Placeholder", description="The placeholder to copy into."),
            Argument("source_language", type=str, description="The language to copy from."),
            Argument("target_language", type=str, description="The language to copy into."),
        ),
    ),
    Operation(
        operations.DELETE_PLUGIN,
        summary=_lazy("Delete a plugin"),
        description="Delete a plugin with its children. Requires permission to delete the plugin.",
        service=delete_plugin,
        arguments=(
            Argument("plugin", model="cms.CMSPlugin", description="The plugin."),
        ),
    ),
    Operation(
        operations.CLEAR_PLACEHOLDER,
        summary=_lazy("Clear a placeholder"),
        description=(
            "Delete all plugins of a placeholder, in one language or in all of them. Requires "
            "permission to clear the placeholder."
        ),
        service=clear_placeholder,
        arguments=(
            Argument("placeholder", model="cms.Placeholder", description="The placeholder to clear."),
            Argument("language", type=str, null=True, description="The language to clear; all languages if null."),
        ),
    ),
    Operation(
        operations.COPY_PLUGIN_TO_CLIPBOARD,
        summary=_lazy("Copy a plugin to the clipboard"),
        description=(
            "Replace the acting user's clipboard with a copy of a plugin and its children. Requires "
            "permission to read the plugin's placeholder and to copy the plugins."
        ),
        service=copy_plugin_to_clipboard,
        arguments=(
            Argument("source_plugin", model="cms.CMSPlugin", description="The plugin to copy, with its descendants."),
            Argument("target_placeholder", model="cms.Placeholder", description="The acting user's clipboard."),
            Argument("target_language", type=str, description="The language of the clipboard."),
        ),
    ),
    Operation(
        operations.COPY_PLACEHOLDER_TO_CLIPBOARD,
        summary=_lazy("Copy a placeholder to the clipboard"),
        description=(
            "Replace the acting user's clipboard with a copy of all plugins of a placeholder in one "
            "language. Requires permission to read the placeholder and to copy the plugins."
        ),
        service=copy_placeholder_to_clipboard,
        arguments=(
            Argument("source_placeholder", model="cms.Placeholder", description="The placeholder to copy."),
            Argument("target_placeholder", model="cms.Placeholder", description="The acting user's clipboard."),
            Argument("source_language", type=str, description="The language to copy."),
            Argument("target_language", type=str, description="The language of the clipboard."),
        ),
    ),
):
    register_operation(_declaration)
del _declaration
